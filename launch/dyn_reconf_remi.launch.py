from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_name = "web_dyn_reconf"

    host_arg = DeclareLaunchArgument(
        "host", default_value="0.0.0.0", description="Host address"
    )
    port_arg = DeclareLaunchArgument(
        "port", default_value="8090", description="Port"
    )
    debug_arg = DeclareLaunchArgument(
        "debug", default_value="False", description="Debug"
    )

    dyn_reconf_remi_node = Node(
        package=pkg_name,
        executable="dyn_reconf_remi.py",
        name="dyn_reconf",
        emulate_tty=True,
        parameters=[
            {"host": LaunchConfiguration("host")},
            {"port": LaunchConfiguration("port")},
            {"debug": LaunchConfiguration("debug")},
        ]
    )

    return LaunchDescription(
        [
            host_arg,
            port_arg,
            debug_arg,
            dyn_reconf_remi_node,
        ]
    )