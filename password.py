import datetime


class Password:
    def __init__(self, password: str, add_date: str = str(datetime.datetime.now().date()), hit_count: int = 0,
                 last_hit_date: str = ''):
        self.password = password  # 密码内容
        self.add_date = add_date  # 添加日期
        self.hit_count = hit_count  # 命中次数
        self.last_hit_date = last_hit_date  # 最后一次命中日期

    def hit(self):
        """记录密码命中"""
        self.hit_count += 1
        self.last_hit_date = str(datetime.datetime.now().date())


def sort_passwords(passwords: list, last_hit_weight: float) -> list:
    """
    按命中次数和最后命中日期排序密码列表
    
    Args:
        passwords: Password对象列表
        last_hit_weight: 最后命中日期权重
        
    Returns:
        排序后的Password列表
    """
    now = datetime.datetime.now().date()

    def get_score(pwd: Password) -> float:
        # 基础分为命中次数
        score = pwd.hit_count

        # 如果有最后命中日期,计算距今天数并加权
        if pwd.last_hit_date:
            str_hit = datetime.datetime.strptime(pwd.last_hit_date, "%Y-%m-%d").date()
            days = (now - str_hit).days
            score /= 1 + days * last_hit_weight

        return score

    # 按得分从高到低排序
    return sorted(passwords, key=get_score, reverse=True)


##- 如果你的密码库更新频繁，建议使用 `-0.3` 到 `-0.5` 之间的值
##- 如果你的密码库更新不频繁，建议使用 `-0.1` 到 `-0.2` 之间的值


def read_password():
    tmp = []
    with open("password.txt", "r", encoding='utf-8') as file:
        for line in file.readlines():
            line = line.strip('\n')  # 去掉列表中每一个元素的换行符
            str_pw = line.split("\t")
            if str_pw.__len__() > 1:
                pw = Password(str_pw[0], str_pw[1], int(str_pw[2]), str_pw[3])
            else:
                pw = Password(str_pw[0])
            tmp.append(pw)
    file.close()
    return tmp


def write_password(passwords: list[Password]):
    with open("password.txt", "w", encoding='utf-8') as file:
        for password in passwords:
            str_pw = password.password + "\t" + password.add_date + "\t" + str(
                password.hit_count) + "\t" + password.last_hit_date
            file.write(str_pw + "\n")
    file.close()


def get_str_passwords(passwords: list[Password]):
    str_passwords = []
    for password in passwords:
        str_passwords.append(password.password)
    return str_passwords


def hit_password(passwords: list[Password], str_password: str):
    for password in passwords:
        if password.password == str_password:
            password.hit()
            return True
    return False
