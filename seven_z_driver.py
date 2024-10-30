import os
import re
import subprocess

import file_ops


class SevenZDriver:
    def __init__(self, location_path=r'C:\Program Files\7-Zip\7z.exe'):
        self.location_path = location_path

    def unzip(self, compress_file, output_file, password, output_path, jap, covered):
        # x 解压  -p 使用密码 -y 重复文件不询问直接覆盖 -o 输出路径 -mcp 编码代码
        cmd = [self.location_path, 'x', '-p{}'.format(password), '-y', compress_file]
        if output_file:  # 解压压缩包内的指定文件
            cmd.append(output_file)
            parent = output_file.split("\\")[0]
            if os.path.join(output_path, parent) == compress_file:
                parent += "(1)"
                output_path = os.path.join(output_path, parent)
        if jap:
            # 使用SHIFT_JIS编码解压
            cmd.append('-mcp=932')
        if covered:
            cmd.append('-t#')
        cmd.append('-o{}'.format(output_path))

        print(cmd)
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        out, err = result.communicate()
        msg = None
        if err:
            # print(err.decode('gbk'))
            msg = err.decode('gbk')
        else:
            # print(out.decode('gbk'))
            msg = out.decode('gbk')
        return result.returncode, msg

    def get_namelist(self, file_path, password, jap=False, covered=False):
        pattern = r'^20\d{2}-[01]\d-[0-3]\d [0-2]\d:[0-6]\d:[0-6]\d \.\S{4}.{28}(.+?)[\r\n]'

        namelist = []
        cmd = [self.location_path, 'l', file_path, '-p{}'.format(password)]

        if jap:
            # 使用SHIFT_JIS编码解压
            cmd.append('-mcp=932')
        if covered:
            cmd.append('-t#')
            pattern = r'^ {20}.\S{4}.{28}(.+?)[\r\n]'
            print(cmd)
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    close_fds=True).communicate()
        if err:
            msg = err.decode('gbk')
            raise GetNamelistError(f'获取文件list错误:{msg}')
        if out:
            for line in out.strip().decode('gbk').split('\n'):
                match = re.search(pattern, line)
                if match:
                    file = match.group(1)
                    if not jap and file_ops.encode_detect(file):
                        raise JapDecodeError(f'文件名乱码:{file}')
                    if file not in namelist:
                        file = re.sub(r'[〜？！_]', "?", file)
                        file = file.replace(u'\u3000', "?").replace(u'\xa0', "?")
                        namelist.append(file)
                elif 'Type = 7z' in line:
                    # 7z自带多核优化，无需namelist直接全部解压效率最高
                    namelist = ['*']
                    break
        return namelist


class JapDecodeError(Exception):
    def __init__(self, error_info):
        super(JapDecodeError, self).__init__(error_info)
        self.error_info = error_info

    def __str__(self):
        return self.error_info


class GetNamelistError(Exception):
    def __init__(self, error_info):
        super(GetNamelistError, self).__init__(error_info)
        self.error_info = error_info

    def __str__(self):
        return self.error_info
