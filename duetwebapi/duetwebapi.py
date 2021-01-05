
import requests
import json


class DuetWebAPI:
    def __init__(self, printer_url):
        self.__printer_url = printer_url

        try:
            requests.get(f'{self.__printer_url}/rr_status?type=1')
            self.__printer_type = 2
        except requests.exceptions.RequestException:

            try:
                requests.get(f'{self.__printer_url}/machine/status')
                self.__printer_type = 3
            except requests.exceptions.RequestException:
                raise ValueError('RRF2 or RRF3 printer cannot be reached')

    def printer_type(self):
        return self.__printer_type

    def printer_url(self):
        return self.__printer_url

    def get_coords(self):
        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_status?type=2')
            reply = json.loads(request.text)
            reply_coords = reply['coords']['xyz']
            reply_axis_names = reply['axisNames']
            ret = {}
            for i in range(len(reply_coords)):
                ret[reply_axis_names[i]] = reply_coords[i]
            return ret

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/status')
            reply = json.loads(request.text)
            reply_axes = reply['axes']
            ret = {}
            for i in range(len(reply_axes)):
                ret[reply_axes[i]['letter']] = reply_axes[i]['userPosition']
            return ret

    def get_layer(self):
        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_status?type=3')
            reply = json.loads(request.text)
            ret = reply['currentLayer']
            return ret

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/status')
            reply = json.loads(request.text)
            ret = reply['job']['layer']
            if ret is None:
                ret = 0
            return ret

    def get_g10_tool_offsets(self, tool):
        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_status?type=2')
            reply = json.loads(request.text)
            reply_axis_names = reply['axisNames']
            reply_tools = reply['tools']
            tool_offsets = reply_tools[tool]['offsets']
            ret = {}
            for i in range(len(tool_offsets)):
                ret[reply_axis_names[i]] = tool_offsets[i]
            return ret

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/status')
            reply = json.loads(request.text)
            reply_axes = reply['move']['axes']
            reply_tools = reply['tools']
            tool_offsets = reply_tools[tool]['offsets']
            ret = {}
            for i in range(len(tool_offsets)):
                ret[reply_axes[i]['letter']] = tool_offsets[i]
            return ret

    def get_extruder_count(self):
        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_status?type=2')
            reply = json.loads(request.text)
            return len(reply['coords']['extr'])

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/status')
            reply = json.loads(request.text)
            return len(reply['move']['extruders'])

    def get_tool_count(self):
        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_status?type=2')
            reply = json.loads(request.text)
            return len(reply['tools'])

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/status')
            reply = json.loads(request.text)
            return len(reply['tools'])

    def get_status(self):
        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_status?type=2')
            reply = json.loads(request.text)
            status = reply['status']
            if 'I' in status:
                return 'idle'
            elif 'P' in status:
                return 'processing'
            elif 'S' in status:
                return 'paused'
            elif 'B' in status:
                return 'cancelling'
            else:
                return status

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/status')
            reply = json.loads(request.text)
            return len(reply['state']['status'])

    def g_code(self, command):
        request = None

        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_gcode?gcode={command}')

        elif self.__printer_type == 3:
            request = requests.post(f'{self.__printer_url}/machine/code/', data=command)

        if request.ok:
            return 0
        else:
            print(f'gCode command returns code: {request.status_code}')
            print(request.reason)
            return request.status_code

    def get_file(self, filename):
        request = None

        if self.__printer_type == 2:
            request = requests.get(f'{self.__printer_url}/rr_download?name={filename}')

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/file/{filename}')

        return request.text.splitlines()

    def get_temperatures(self):
        if self.__printer_type == 2:
            # request = requests.get(f'{self.__printer_url}/rr_status?type=2')
            # reply = json.loads(request.text)
            return 'Error: get_temperatures no implemented for RRF2 printers'

        elif self.__printer_type == 3:
            request = requests.get(f'{self.__printer_url}/machine/status')
            reply = json.loads(request.text)
            return reply['sensors']['analog']

    def test_all(self):
        print(self.printer_type())
        print(self.get_coords())
        print(self.get_g10_tool_offsets(0))
        print(self.get_extruder_count())
        print(self.get_tool_count())
        print(self.get_status())
        print(self.g_code('T'))
        print(self.get_file('sys/config.g'))
        print(self.get_temperatures())
