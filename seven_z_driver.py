import os
import re
import subprocess

import file_ops


class SevenZDriver:
    def __init__(self, location_path=r'C:\Program Files\7-Zip\7z.exe'):
        self.location_path = location_path

    def unzip(self, compress_file: str, output_path: str, password: str = '', output_file: str = None,
              jap: bool = False,
              covered: bool = False):
        if not compress_file:
            raise UnzipError('压缩文件未设置')
        if not output_path:
            raise UnzipError('输出路径未设置')
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
        if err:
            # print(err.decode('gbk'))
            msg = err.decode('gbk')
            if "Wrong password" not in msg:
                if "No files to process" in msg:
                    raise NoFile2ProcessError(msg)
                raise UnzipError(msg)
            elif "Cannot delete output file" in msg:
                raise CannotDeleteOutputFile(msg)
        else:
            # print(out.decode('gbk'))
            # msg = out.decode('gbk')
            msg = password
        return result.returncode, msg

    def get_namelist(self, compress_file: str, password: str = '', jap: bool = False, covered: bool = False):
        # if not compress_file:
        #     raise UnzipError('压缩文件未设置')
        pattern = r'^20\d{2}-[01]\d-[0-3]\d [0-2]\d:[0-6]\d:[0-6]\d \.\S{4}.{28}(.+?)[\r\n]'
        ratio_pattern = r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+(\d+)\s+(\d+)\s+\d+\s+files(?:,\s+\d+\s+folders)?\s*$'
        namelist = []
        compression_ratio_info = {}
        cmd = [self.location_path, 'l', compress_file, '-p{}'.format(password)]

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
            compression_ratio_info = {"encrypted": False}
            for line in out.strip().decode('gbk').split('\n'):
                match = re.search(pattern, line)
                if match:
                    file = match.group(1)
                    if not jap and file_ops.encode_detect(file):
                        raise JapDecodeError(f'文件名乱码:{file}')
                    if file not in namelist:
                        file = re.sub(r'[〜？！_ ′]', "?", file)
                        file = file.replace(u'\u3000', "?").replace(u'\xa0', "?")
                        namelist.append(file)
                else:
                    match = re.match(ratio_pattern, line)
                    if match:
                        size = int(match.group(1))  # 解压后大小
                        compressed = int(match.group(2))  # 压缩后大小
                        # 计算压缩率
                        compression_ratio = (compressed / size * 100) if size > 0 else 0
                        compression_ratio_info.update({
                            "size": size,
                            "compressed": compressed,
                            "compression_ratio": round(compression_ratio, 2)
                        })
                    elif '7zAES' in line:
                        compression_ratio_info["encrypted"] = True

        return namelist, compression_ratio_info


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


class CannotDeleteOutputFile(EOFError):
    def __init__(self, error_info):
        super(CannotDeleteOutputFile, self).__init__(error_info)
        self.error_info = error_info

    def __str__(self):
        return self.error_info
