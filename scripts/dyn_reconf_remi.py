#!/usr/bin/env python3
import rclpy
import remi.gui as gui

from remi.server import start
from remi import App
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import  ParameterValue, Parameter as SrvParam
from rcl_interfaces.srv import GetParameters
from rcl_interfaces.srv import ListParameters, GetParameters, DescribeParameters, SetParameters

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 25

NAME_L_SIZE = -1
MIN_L_SIZE = -1
EDIT1_SIZE = -1
MAX_L_SIZE = -1
EDIT2_SIZE = -1
FIELD_HEIGHT = -1
SLIDER_SIZE = 300


class MyApp(App):
    def __init__(self, *args):
        self.node = node
        super(MyApp, self).__init__(*args)

    def main(self, name="world"):
        self.wid = gui.Widget(layout_orientation=gui.Container.LAYOUT_VERTICAL)

        self.hor_servers = gui.Widget(layout_orientation=gui.Container.LAYOUT_HORIZONTAL)
        self.bt = gui.Button("Refresh Node List")
        self.bt.onclick.do(self.refresh_nodes)

        self.hor_servers.add_child(1, self.bt)
        self.bt.style["display"] = "block"
        self.bt.style["margin"] = "10px auto"
        self.bt.style["float"] = "none"

        self.refresh_nodes()

        return self.wid

    def on_dropdown_change(self, widget, value):
        if value == "Choose node...":
            return
        clients_to_destroy = []

        node_name = value

        try:
            cli_list = node.create_client(ListParameters, f"{value}/list_parameters")
            clients_to_destroy.append(cli_list)

            if not cli_list.wait_for_service(timeout_sec=1.0):
                self.notification_message("Fail", f"Failed to get service {value}/get_parameters")
                return

            list_request = ListParameters.Request()
            list_request.depth = 0
            future_list = cli_list.call_async(list_request)
            rclpy.spin_until_future_complete(node, future_list)

            if future_list.result() is None:
                return

            table = gui.Table()
            row = gui.TableRow()

            headers = ["Param name", "Min", "Edit", "Max", "Value", "Set"]
            for i, header in enumerate(headers):
                item = gui.TableTitle()
                item.add_child(str(id(item)), header)
                row.add_child(str(id(item)), item)
            table.add_child(str(id(row)), row)

            cli = node.create_client(GetParameters, f"{value}/get_parameters")
            clients_to_destroy.append(cli)

            if not cli.wait_for_service(timeout_sec=1.0):
                self.notification_message("Fail", f"Failed to get service {value}/get_parameters")
                return

            parameter_get_req = GetParameters.Request()
            parameter_get_req.names = [name for name in future_list.result().result.names]
            param_get_result = cli.call_async(parameter_get_req)
            rclpy.spin_until_future_complete(node, param_get_result)

            desc_cli = node.create_client(DescribeParameters, f"{value}/describe_parameters")
            clients_to_destroy.append(desc_cli)
            if not desc_cli.wait_for_service(timeout_sec=1.0):
                node.get_logger().info("describe_parameters service not available, waiting...")
                self.notification_message("Fail", f"Failed to get service {value}/describe_parameters")
                return

            desc_req = DescribeParameters.Request()
            desc_req.names = parameter_get_req.names
            desc_future = desc_cli.call_async(desc_req)
            rclpy.spin_until_future_complete(node, desc_future)

            if param_get_result.result() is None or desc_future.result() is None:
                self.notification_message("Fail", f"Failed to get parameters or description parameters")
                return

            for idx, param in enumerate(param_get_result.result().values):
                row = gui.TableRow()

                name_cell = gui.TableItem()
                name_cell.add_child(0, gui.Label(parameter_get_req.names[idx], width=NAME_L_SIZE, height=FIELD_HEIGHT))
                row.add_child(str(id(name_cell)), name_cell)

                min_cell = gui.TableItem()
                row.add_child(1, min_cell)

                value_cell = gui.TableItem()
                row.add_child(2, value_cell)

                max_cell = gui.TableItem()
                row.add_child(3, max_cell)


                edti2_cell = gui.TableItem()
                row.add_child(4, edti2_cell)

                update_cell = gui.TableItem()
                row.add_child(5, update_cell)

                set_btn = gui.Button("set", width=100)

                param_name = parameter_get_req.names[idx]

                min_val, max_val, edit_item2 = None, None, None

                if param.type == Parameter.Type.BOOL.value:
                    value_item = gui.CheckBox(checked=param.bool_value)
                    set_btn.onclick.do(self.create_param_callback(value_item, node_name, param_name, param.type))
                elif param.type == Parameter.Type.INTEGER.value:
                    min_v, max_v = -100_000, 100_000
                    if len(desc_future.result().descriptors[idx].integer_range) != 0:
                        min_v, max_v = desc_future.result().descriptors[idx].integer_range

                    min_val = gui.Label(str(min_v), width=MIN_L_SIZE, height=FIELD_HEIGHT)
                    max_val = gui.Label(str(min_v), width=MIN_L_SIZE, height=FIELD_HEIGHT)

                    value_item = gui.Slider(width=SLIDER_SIZE, height=FIELD_HEIGHT, default_value=param.integer_value, min=min_v, max=max_v, step=1)

                    edit_item2 = gui.SpinBox(width=EDIT2_SIZE, height=FIELD_HEIGHT,
                                        default_value=param.integer_value,
                                        min=min_v, max=max_v, step=1)
                    value_item.onchange.do(self.update_widget_from_slider(widget_edit=edit_item2))
                    edit_item2.onchange.do(self.update_slider_from_edit(widget_slider=value_item))
                    set_btn.onclick.do(self.create_param_callback(value_item, node_name, param_name, param.type))

                elif param.type == Parameter.Type.DOUBLE.value:
                    min_v, max_v = -100_000.0, 100_000.0
                    if len(desc_future.result().descriptors[idx].floating_point_range) != 0:
                        min_v, max_v = desc_future.result().descriptors[idx].floating_point_range

                    min_val = gui.Label(str(min_v), width=MIN_L_SIZE, height=FIELD_HEIGHT)
                    max_val = gui.Label(str(min_v), width=MIN_L_SIZE, height=FIELD_HEIGHT)

                    value_item = gui.Slider(
                        width=SLIDER_SIZE, height=FIELD_HEIGHT, default_value=param.double_value, min=min_v, max=max_v, step=0.1
                    )
                    edit_item2 = gui.SpinBox(width=EDIT2_SIZE, height=FIELD_HEIGHT,
                                        default_value=param.double_value,
                                        min=min_val, max=max_val, step=0.1)
                    value_item.onchange.do(self.update_widget_from_slider(widget_edit=edit_item2))
                    edit_item2.onchange.do(self.update_slider_from_edit(widget_slider=value_item))
                    set_btn.onclick.do(self.create_param_callback(value_item, node_name, param_name, param.type))

                elif param.type == Parameter.Type.STRING.value:
                    value_item = gui.TextInput(width=MAX_L_SIZE, height=FIELD_HEIGHT, single_line=True)
                    value_item.set_text(param.string_value)
                    set_btn.onclick.do(self.create_param_callback(value_item, node_name, param_name, param.type))
                else:
                    value_item = gui.Label("Unsupported type")


                if min_val is not None:
                    min_cell.add_child(1, min_val)
                value_cell.add_child(2, value_item)
                if max_val is not None:
                    max_cell.add_child(3, max_val)
                if edit_item2 is not None:
                    edti2_cell.add_child(4, edit_item2)

                update_cell.add_child(5, set_btn)

                table.add_child(str(id(row)), row)

            if hasattr(self, "param_table"):
                self.wid.remove_child(self.param_table)

            self.param_table = table
            self.wid.add_child(2, table)
            table.style["margin"] = "10px auto"
        except Exception as e:
            self.notification_message("Unnown error", str(e))
        finally:
            for client in clients_to_destroy:
                node.destroy_client(client)

    def update_widget_from_slider(self, widget_edit: gui.TextInput):
        def callback(widget, new_value):
            widget_edit.set_value(new_value)
            pass

        return callback

    def update_slider_from_edit(self, widget_slider: gui.Slider):
        def callback(widget, new_value):
            widget_slider.set_value(new_value)
            pass

        return callback

    def create_param_callback(self, widget_value, node_name, param_name, param_type):
        def callback(widget):
            try:
                v = ParameterValue(type=param_type)
                if param_type == Parameter.Type.BOOL.value:
                    v.bool_value = widget_value.get_value()
                elif param_type == Parameter.Type.STRING.value:
                    v.string_value = widget_value.get_value()
                elif param_type == Parameter.Type.DOUBLE.value:
                    v.double_value = float(widget_value.get_value())
                elif param_type == Parameter.Type.INTEGER.value:
                    v.integer_value = int(widget_value.get_value())
                else:
                    self.notification_message("Fail", f"Parameter type is not supported")
                    return

                param = SrvParam(name=param_name, value=v)
                set_cli = node.create_client(SetParameters, f"{node_name}/set_parameters")
                if not set_cli.wait_for_service(timeout_sec=1.0):
                    self.notification_message("Fail", f"Service {node_name}/set_parameters not avaiable")
                    return

                req = SetParameters.Request()
                req.parameters = [param]

                future = set_cli.call_async(req)
                rclpy.spin_until_future_complete(self.node, future)
                if future.result() is None:
                    self.notification_message("Fail", "Failed to call service")
                elif future.result().results[0].successful is False:
                    self.notification_message("Fail", f"Reason: {future.result().results[0].reason}")
                else:
                    self.notification_message("Success", f"Param {param_name} set")

            except Exception as e:
                self.node.get_logger().error(f"Error setting parameter {param_name}: {e}")
            finally:
                self.node.destroy_client(set_cli)

        return callback

    def refresh_nodes(self, args=None):
        node_names = self.node.get_node_names()

        self.dropdown = gui.DropDown()
        choose_ddi = gui.DropDownItem("Choose node...")
        self.dropdown.add_child(0, choose_ddi)

        for idx, node_name in enumerate(node_names):
            ddi = gui.DropDownItem(node_name)
            self.dropdown.add_child(idx + 1, ddi)

        self.dropdown.onchange.do(self.on_dropdown_change)
        self.hor_servers.add_child(2, self.dropdown)
        self.dropdown.style["display"] = "block"
        self.dropdown.style["margin"] = "10px auto"
        self.dropdown.style["float"] = "none"
        self.wid.add_child(1, self.hor_servers)

    def on_close(self):
        self.node.get_logger().info("shutdown node")
        if self.node:
            self.node.destroy_node()
        rclpy.shutdown()


def main(args=None):
    global node
    rclpy.init(args=args)
    node = Node("web_dyn_reconf")
    host = node.declare_parameter("host", "0.0.0.0").value
    port = node.declare_parameter("port", 8090).value
    debug = node.declare_parameter("debug", False).value

    node.get_logger().warn(str(debug))
    start(MyApp, address=host, port=port, multiple_instance=True, start_browser=False, debug=debug)


if __name__ == "__main__":
    main()
