#!/usr/bin/env python3
"""Odin1 Lite v3.x 服务客户端，在厂家驱动所在主机运行。"""
import argparse
import math
from pathlib import Path
import re
import sys


def build_steps(action, path=''):
    """检查输入，按调用顺序生成服务请求。"""
    modes = {'normal': 1, 'slam': 3, 'relocate': 4, 'remap': 5}
    if action not in (*modes, 'save', 'export'):
        raise ValueError('Unknown action: ' + action)
    steps = []
    if action in ('relocate', 'remap', 'save', 'export'):
        file = Path(path).expanduser()
        if not path or not file.is_absolute():
            raise ValueError('Map path must be absolute on the driver host')
        if action != 'export' and file.suffix.lower() != '.bin':
            raise ValueError('SLAM maps must use .bin; they are not Nav2 YAML maps')
        if action in ('relocate', 'remap') and not file.is_file():
            raise ValueError('Input map does not exist: ' + str(file))
        if action in ('save', 'export') and not file.parent.is_dir():
            raise ValueError('Output directory does not exist: ' + str(file.parent))
        path = str(file)
    if action in modes:
        steps.append(('device_mode', 'DeviceMode', {'mode': modes[action]}))
    if action in ('relocate', 'remap'):
        steps.append(('load_map', 'LoadMap', {'path': path}))
    elif action == 'save':
        steps.append(('save_map', 'SaveMap', {'path': path}))
    elif action == 'export':
        # 厂家服务名拼写为 exploy_map。
        steps.append(('exploy_map', 'ExployMap', {'path': path}))
    return steps


def execute_steps(steps, call):
    """按顺序调用服务，失败时由异常中止后续请求。"""
    for service, kind, fields in steps:
        call(service, kind, fields)


def checked_response(response, service):
    if response is None:
        raise RuntimeError(service + ': no response (timeout or transport failure)')
    if not response.success or response.error_code != 0:
        raise RuntimeError(f'{service}: {response.error_code}: {response.message}')
    return response.message


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['normal', 'slam', 'save', 'relocate', 'remap', 'export'])
    parser.add_argument('--path', default='')
    parser.add_argument('--prefix', default='/manifold/device0')
    parser.add_argument('--timeout', type=float, default=30.0)
    args = parser.parse_args(argv)
    try:
        steps = build_steps(args.action, args.path)
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError('Timeout must be finite and positive')
        prefix = '/' + args.prefix.strip('/')
        if not re.fullmatch(r'(?:/[A-Za-z_][A-Za-z0-9_]*)+', prefix):
            raise ValueError('Prefix must be a ROS service namespace, e.g. /manifold/device0')
    except ValueError as error:
        parser.error(str(error))

    try:
        import rclpy
        from odin_ros_driver_rev1 import srv
    except ImportError as error:
        print('Source ROS 2 and the official Odin driver workspace first: ' + str(error), file=sys.stderr)
        return 1
    rclpy.init(args=[])
    node = rclpy.create_node('sentry_odin_control')
    def call(service, kind, fields):
        client = node.create_client(getattr(srv, kind), prefix + '/' + service)
        try:
            if not client.wait_for_service(timeout_sec=args.timeout):
                raise RuntimeError(service + ': service unavailable; check driver/device/algorithm SDK')
            request = getattr(srv, kind).Request()
            for key, value in fields.items():
                setattr(request, key, value)
            future = client.call_async(request)
            rclpy.spin_until_future_complete(node, future, timeout_sec=args.timeout)
            if not future.done():
                future.cancel()
                raise RuntimeError(service + ': timed out; device state may have changed, check before retrying')
            message = checked_response(future.result(), service)
            print(service + ': ' + message)
        finally:
            node.destroy_client(client)
    try:
        execute_steps(steps, call)
        return 0
    except (RuntimeError, AttributeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    sys.exit(main())
