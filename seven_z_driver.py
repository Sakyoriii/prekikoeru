import os
import re
import subprocess

import file_ops


class SevenZDriver:
    def __init__(self, location_path=r'C:\Program Files\7-Zip\7z.exe'):
        self.location_path = location_path
        self.compress_file=None
        self.output_file=None
        self.output_path=None
        self.password=None
        self.jap=False
        self.covered=False

    def set_compress_file(self, compress_file):
        self.compress_file=compress_file
        return self
    
    def set_output_file(self, output_file):
        self.output_file=output_file
        return self
    
    def set_output_path(self, output_path):
        self.output_path=output_path
        return self

    def set_password(self, password):
        self.password=password
        return self
    
    def set_jap(self, jap:bool):
        self.jap=jap
        return self
    
    def set_covered(self, covered:bool):
        self.covered=covered
        return self

    def unzip(self):
        if not self.compress_file:
            raise UnzipError('压缩文件未设置')
        if not self.output_path:
            raise UnzipError('输出路径未设置')
        # x 解压  -p 使用密码 -y 重复文件不询问直接覆盖 -o 输出路径 -mcp 编码代码
        cmd = [self.location_path, 'x', '-p{}'.format(self.password), '-y', self.compress_file]
        if self.output_file:  # 解压压缩包内的指定文件
            cmd.append(self.output_file)
            parent = self.output_file.split("\\")[0]
            if os.path.join(self.output_path, parent) == self.compress_file:
                parent += "(1)"
                self.output_path = os.path.join(self.output_path, parent)
        if self.jap:
            # 使用SHIFT_JIS编码解压
            cmd.append('-mcp=932')
        if self.covered:
            cmd.append('-t#')
        cmd.append('-o{}'.format(self.output_path))

        print(cmd)
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        out, err = result.communicate()
        if err:
            # print(err.decode('gbk'))
            msg = err.decode('gbk')
            if "Wrong password" not in msg:
                if "No files to process" in msg:
                    raise NoFile2ProcessError(msg)
                raise UnzipError(msg)
        else:
            # print(out.decode('gbk'))
            msg = out.decode('gbk')
        return result.returncode, msg

    def get_namelist(self):
        if not self.compress_file:
            raise UnzipError('压缩文件未设置')
        pattern = r'^20\d{2}-[01]\d-[0-3]\d [0-2]\d:[0-6]\d:[0-6]\d \.\S{4}.{28}(.+?)[\r\n]'

        namelist = []
        cmd = [self.location_path, 'l', self.compress_file, '-p{}'.format(self.password)]

        if self.jap:
            # 使用SHIFT_JIS编码解压
            cmd.append('-mcp=932')
        if self.covered:
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
                    if not self.jap and file_ops.encode_detect(file):
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


class UnzipError(Exception):
    def __init__(self, error_info):
        super(UnzipError, self).__init__(error_info)
        self.error_info = error_info

    def __str__(self):
        return self.error_info


class NoFile2ProcessError(EOFError):
    def __init__(self, error_info):
        super(NoFile2ProcessError, self).__init__(error_info)
        self.error_info = error_info

    def __str__(self):
        return self.error_info
