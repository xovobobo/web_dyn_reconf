#!/usr/bin/env python3
import rclpy
import remi.gui as gui

from remi.server import start
from remi import App
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import ParameterValue, Parameter as SrvParam
from rcl_interfaces.srv import GetParameters
from rcl_interfaces.srv import ListParameters, GetParameters, DescribeParameters, SetParameters

DEFAULT_HEIGHT = 25


class Popup(gui.VBox):
    def __init__(self, title, message, *args, **kwargs):
        gui.VBox.__init__(self, *args, **kwargs)
        self.css_display = "none"
        self.style["margin"] = "auto"
        self.style["border"] = "3px solid gray"
        self.css_outline = "3px solid gray"

        self.title = gui.Label(title, style={"font-weight": "bold"})
        self.message = gui.Label(message, style={"font-size": "15px"})

        self.append(self.title)
        self.append(self.message)

        self.bt_confirm = gui.Button("Confirm")
        self.bt_confirm.onclick.do(self.onconfirm)
        self.append(self.bt_confirm)

    @gui.decorate_event
    def onconfirm(self, emitter):
        self.css_display = "none"
        return ()

    def show(self, title, message):
        self.title.set_text(title)
        self.message.set_text(message)
        self.css_position = "absolute"
        self.css_display = "flex"


class MyApp(App):
    def __init__(self, *args):
        self.node = node
        super(MyApp, self).__init__(*args)

    def main(self, name="world"):
        self.main_container = gui.VBox(style={"margin": "0px auto", "width": "100%"})

        self.wid = gui.Widget(layout_orientation=gui.Container.LAYOUT_VERTICAL)
        self.wid.style["width"] = "100%"
        self.hor_servers = gui.Widget(layout_orientation=gui.Container.LAYOUT_HORIZONTAL)
        self.bt = gui.Button("Refresh Node List")
        self.bt.onclick.do(self.refresh_nodes)

        self.popup = Popup("q", "qq")
        self.main_container.append(self.wid),
        self.main_container.append(self.popup)

        self.hor_servers.add_child(1, self.bt)
        self.bt.style["display"] = "block"
        self.bt.style["margin"] = "10px auto"
        self.bt.style["float"] = "none"

        self.refresh_nodes()

        return self.main_container

    def create_num_row(self, node_name: str, param_descr, param_value: ParameterValue) -> gui.TableRow:
        row = gui.TableRow(height=DEFAULT_HEIGHT)
        row.set_style({"margin": "5px 0", "vertical-align": "middle"})

        name_cell = gui.TableItem()
        name_cell.add_child(0, gui.Label(param_descr.name))
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

        set_btn = gui.Button("set")
        update_cell.set_style(
            {
                "padding": "0",
                "margin": "0",
                "box-sizing": "border-box",
            }
        )
        set_btn.set_style(
            {
                "width": "100%",
                "height": "100%",
            }
        )

        update_cell.add_child(5, set_btn)
        if param_descr.type == Parameter.Type.BOOL.value:
            value_item = gui.CheckBox(checked=param_value.bool_value)
            set_btn.onclick.do(self.create_param_callback(value_item, node_name, param_descr.name, param_value.type))
        elif param_descr.type == Parameter.Type.INTEGER.value:
            min_v, max_v = -100_000, 100_000
            if len(param_descr.integer_range) != 0:
                min_v, max_v = param_descr.integer_rang
            min_val = gui.Label(str(min_v))
            max_val = gui.Label(str(min_v))

            min_cell.add_child(1, min_val)
            value_item = gui.Slider(width="100%", default_value=param_value.integer_value, min=min_v, max=max_v, step=1)
            max_cell.add_child(3, max_val)

            edit_item2 = gui.SpinBox(default_value=param_value.integer_value, min=min_v, max=max_v, step=1)
            edti2_cell.add_child(4, edit_item2)

            value_item.onchange.do(self.update_widget_from_slider(widget_edit=edit_item2))
            edit_item2.onchange.do(self.update_slider_from_edit(widget_slider=value_item))
            set_btn.onclick.do(self.create_param_callback(edit_item2, node_name, param_descr.name, param_descr.type))

        elif param_descr.type == Parameter.Type.DOUBLE.value:
            min_v, max_v = -100_000.0, 100_000.0
            if len(param_descr.floating_point_range) != 0:
                min_v, max_v = param_descr.floating_point_range

            min_val = gui.Label(str(min_v))
            max_val = gui.Label(str(min_v))

            min_cell.add_child(1, min_val)
            value_item = gui.Slider(width="100%", default_value=param_value.double_value, min=min_v, max=max_v, step=0.1)
            max_cell.add_child(3, max_val)

            edit_item2 = gui.SpinBox(default_value=param_value.double_value, min=min_val, max=max_val, step=0.1)
            edti2_cell.add_child(4, edit_item2)

            value_item.onchange.do(self.update_widget_from_slider(widget_edit=edit_item2))
            edit_item2.onchange.do(self.update_slider_from_edit(widget_slider=value_item))
            set_btn.onclick.do(self.create_param_callback(edit_item2, node_name, param_descr.name, param_descr.type))

        elif param_descr.type == Parameter.Type.STRING.value:
            value_item = gui.TextInput(single_line=True)
            value_item.set_text(param_value.string_value)
            value_item.set_style({"text-align": "center"})
            set_btn.onclick.do(self.create_param_callback(value_item, node_name, param_descr.name, param_descr.type))
        else:
            value_item = gui.Label("Unsupported type")

        value_cell.add_child(2, value_item)
        return row

    def get_node_parameters(self, node_name: str):
        clients_to_destroy = []
        try:
            cli_list = node.create_client(ListParameters, f"{node_name}/list_parameters")
            clients_to_destroy.append(cli_list)

            if not cli_list.wait_for_service(timeout_sec=1.0):
                self.popup.show("Fail", f"Service {node_name}/get_parameters is not avaiable")
                return

            list_request = ListParameters.Request()
            list_request.depth = 0
            list_request_future = cli_list.call_async(list_request)
            rclpy.spin_until_future_complete(node, list_request_future)

            if list_request_future.result() is None:
                self.popup.show("Fail", f"Failed to get list of params {node_name}/get_parameters")
                return

            cli = node.create_client(GetParameters, f"{node_name}/get_parameters")
            clients_to_destroy.append(cli)

            if not cli.wait_for_service(timeout_sec=1.0):
                self.popup.show("Fail", f"Service {node_name}/get_parameters is not avaiable")
                return

            parameter_get_req = GetParameters.Request()
            parameter_get_req.names = [name for name in list_request_future.result().result.names]
            get_param_future = cli.call_async(parameter_get_req)
            rclpy.spin_until_future_complete(node, get_param_future)

            desc_cli = node.create_client(DescribeParameters, f"{node_name}/describe_parameters")
            clients_to_destroy.append(desc_cli)
            if not desc_cli.wait_for_service(timeout_sec=1.0):
                self.popup.show("Fail", f"Service {node_name}/describe_parameters is not avaiable")
                return

            desc_req = DescribeParameters.Request()
            desc_req.names = parameter_get_req.names
            desc_future = desc_cli.call_async(desc_req)
            rclpy.spin_until_future_complete(node, desc_future)

            if get_param_future.result() is None or desc_future.result() is None:
                self.popup.show("Fail", f"Failed to get parameters or description parameters")
                return
            return get_param_future.result(), desc_future.result()
        except Exception as e:
            self.popup.show("Unnown error", str(e))
        finally:
            for client in clients_to_destroy:
                self.node.destroy_client(client)

    def on_dropdown_change(self, widget, value):
        if value == "Choose node...":
            return
        node_name = value

        node_data = self.get_node_parameters(node_name)
        if node_data is None:
            return
        param_values, param_descrs = node_data

        table = gui.Table()
        table.style["width"] = "100%"
        header_row = gui.TableRow()
        headers = ["Param name", "Min", "Edit", "Max", "Value", "Set"]
        for i, header in enumerate(headers):
            item = gui.TableTitle()
            item.add_child(str(id(item)), header)
            header_row.add_child(str(id(item)), item)
        table.add_child(str(id(header_row)), header_row)

        for idx, param in enumerate(param_values.values):
            row = self.create_num_row(
                node_name=node_name,
                param_descr=param_descrs.descriptors[idx],
                param_value=param,
            )
            table.add_child(str(id(row)), row)

        if hasattr(self, "param_table"):
            self.wid.remove_child(self.param_table)

        self.param_table = table
        self.wid.add_child(2, table)
        table.style["margin"] = "10px auto"

    def update_widget_from_slider(self, widget_edit: gui.TextInput):
        def callback(widget, new_value):
            widget_edit.set_value(new_value)

        return callback

    def update_slider_from_edit(self, widget_slider: gui.Slider):
        def callback(widget, new_value):
            widget_slider.set_value(new_value)

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
                    self.popup.show("Fail", f"Parameter type is not supported")
                    return

                param = SrvParam(name=param_name, value=v)
                set_cli = node.create_client(SetParameters, f"{node_name}/set_parameters")
                if not set_cli.wait_for_service(timeout_sec=1.0):
                    self.popup.show("Fail", f"Service {node_name}/set_parameters not avaiable")
                    return

                req = SetParameters.Request()
                req.parameters = [param]

                future = set_cli.call_async(req)
                rclpy.spin_until_future_complete(self.node, future)
                if future.result() is None:
                    self.popup.show("Fail", "Failed to call service")
                elif future.result().results[0].successful is False:
                    self.popup.show("Fail", f"Reason: {future.result().results[0].reason}")
                else:
                    self.popup.show("Success", f"Param {param_name} set")

            except Exception as e:
                self.node.get_logger().error(f"Error setting parameter {param_name}: {e}")
            finally:
                self.node.destroy_client(set_cli)

        return callback

    def refresh_nodes(self, args=None):
        node_names = self.node.get_node_names()

        self.dropdown = gui.DropDown()
        self.dropdown.style["width"] = "300px"
        self.dropdown.style["height"] = "40px"

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
