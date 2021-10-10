# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import os
import json
import re
import datetime
import sqlite3
import time
import msvcrt

# ffmpeg 安装路径 按照当前电脑的安装路径修改
ffmpeg_bin_path = r"D:\soft\ffmpeg-4.4-full_build\bin"

command_ffmpeg = ffmpeg_bin_path + os.path.sep + "ffmpeg.exe"
command_ffprobe = ffmpeg_bin_path + os.path.sep + "ffprobe.exe"
param_ffprobe_stream_info_json = " -select_streams v -show_entries format=duration,size,bit_rate" \
                                 " -show_streams -v quiet -of csv=\"p=0\" -of json "
# 转换命令的参数模版字符串，需要增加4个部分1.输入文件路径 2.帧率 3.码率 4.输出文件
command_ffmpeg_trans = r' -i "%s" -r %d -c:v hevc_nvenc -c:a aac -ar 22050 -b:a 96k -b:v %d -maxrate %d -bufsize %d  -y "%s"'
max_bit_rate = 2 * 1024 * 1024  # 码率上限，该值用于确定最大转换后码率，大于该码率的影片都将转换为此码率，小于此码率的则保持不变
max_fps = 30  # 最大帧率，限制影片的最大帧率，如果为0则不限制
record_log_file = "trans_log.txt"
record_log_db = 'transRecord.db'

record_db_table_create = "CREATE TABLE t_TransRecord (ID INTEGER PRIMARY KEY autoincrement NOT NULL,src_path CHAR(300) NOT NULL, " \
                         "des_path CHAR(300) NOT NULL,b_size INT NOT NULL, a_size INT NOT NULL, d_size INT NOT NULL, " \
                         "trans_begin CHAR(50) NOT NULL,trans_end CHAR(50) NOT NULL,trans_cost CHAR(50) NOT NULL," \
                         "b_fps INT NOT NULL,fps INT NOT NULL, b_rate INT NOT NULL, rate INT NOT NULL, " \
                         "duration INT NOT NULL)"



def log_to_file(x):
    print(x)


def record_trans_result(infos_dict):
    """
        ['src_path'] = file_full_path
        ['des_path'] = new_name
        ['before_size'] = before_size
        ['after_size'] = after_size
        ['diff_size'] = offset_size
        ['trans_begin'] = begin_time.strftime("%Y-%m-%d %H:%M:%S")
        ['trans_end'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
        ['trans_cost'] = end_time - begin_time
        ['before_fps'] = int(format_info["bit_rate"])
        ['fps'] = int(fps_str)
        ['before_rate'] = int(format_info["bit_rate"])
        ['rate'] = bit_rate
        ['duration'] = format_info['duration']
    :param infos_dict:
    :return:
    """
    conn = sqlite3.connect(record_log_db)
    db_op = conn.cursor()
    db_op.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + record_log_db + "'")
    #if db_op.fetchall() == '[]':
    #db_op.execute(record_db_table_create)
    if 'src_path' in infos_dict:
        SQL_Command = "INSERT INTO t_TransRecord (src_path,des_path,b_size,a_size,d_size,trans_begin,trans_end,"\
                      "trans_cost,b_fps,fps,b_rate,rate,duration) VALUES('%s', '%s', %d, %d, %d, '%s', '%s'" \
                      ", '%s', %d, %d, %d, %d, %d);" % (infos_dict['src_path'], infos_dict['des_path'], \
                      infos_dict['before_size'],  infos_dict['after_size'], infos_dict['diff_size'], \
                      infos_dict['trans_begin'],  infos_dict['trans_end'], infos_dict['trans_cost'], \
                      infos_dict['before_fps'], infos_dict['fps'], infos_dict['before_rate'], \
                      infos_dict['rate'], int(float(infos_dict['duration'])))
        db_op.execute(SQL_Command)
        conn.commit()


def parse_media_codec_info(file_full_path):
    """
    通过文件名解析文件的编码信息，以json格式返回
    :param file_full_path: 文件的全路径名称字符串
    :return:  文件信息的json结构体
    """
    if os.path.isfile(file_full_path):
        res = os.popen(command_ffprobe + param_ffprobe_stream_info_json + " -i \"" + file_full_path + "\"")
        json_str = res.read()
        json_media_info = json.loads(json_str)
        return json_media_info
    return ""


def get_bit_rate(cur_bit_rate):
    """
    输入码率，获得被转换后的码率
    :return: 码率的实际值
    """
    if int(cur_bit_rate) > max_bit_rate:
        return max_bit_rate * 0.8
    else:
        return int(cur_bit_rate) * 0.8


def get_bit_rate_name_str(rate):
    """
    获取码率的名称部分字符串
    码率： 单位是MB .3 代表0.3MB = 308k， 大于9MB只显示9， 小于100K也只显示.1
    :param rate: 码率int值
    :return: 码率显示在名称中的字符串
    """
    if rate <= 102400:
        return ".1"
    result = rate / 1024 / 1024
    if result > 1:  # 码率大于1MB
        result = int(result + 0.5)   # 进行四舍五入
        if result > 9:  # 码率大于9MB仅显示9MB
            return "9"
        else:
            return str(result)
    else:  # 码率不足1MB
        result = int((result * 100 + 5) / 10)
        return "."+str(result)


def getInput(timeout=5):
    start_time = time.time()
    input = ''
    while True:
        if msvcrt.kbhit():
            input = msvcrt.getche()
        if len(input) != 0 or (time.time() - start_time) > timeout:
            break
    if len(input) > 0:
        return ord(input)
    else:
        return ord('\0')


def get_fps_name_str(frames, duration):
    """
    获取帧数的字符串信息
    :param frames: 总帧数
    :param duration: 时长
    :return:
    """
    fps = int(float(frames) / float(duration))
    if max_fps != 0 and max_fps < fps:
        fps = max_fps
    if fps > 99:
        first_bit = int(fps / 100 - 1)
        a_val = int(ord('a')) + first_bit
        second_bit = int(fps / 10 % 10)
        return str(chr(a_val) + str(second_bit))
    else:
        return str(fps)


def get_fps_name_strs(rate, rate2):
    if '/s' == rate[-2:]:
        return rate[:-2]
    else:
        its = rate.split('/')
        if its[1] != '0':
            return str(int(int(its[0]) / int(its[1])))
        else:
            its2 = rate2.split('/')
            if its2[1] != '0':
                return str(int(int(its2[0]) / int(its2[1])))
            else:
                return "0"


def get_width_height_name_str(width, height):
    """
    获取分辨率的字符串描述信息
    正常的16：9 显示height数值 + 字母p来描述，其余显示实际的像素量
    大于1440 则采用2K 4K等方式表示
    :param width: 宽度的像素个数
    :param height: 高度的像素个数
    :return: 分辨率描述
    """
    heights = {480: "480p", 720: "720p", 768: "768p", 1080: "1080p", 1440: "2K", 2160: "4K"}

    if width < height:
        return ""
    if height in heights:
        if int(int(width) / 10) == int(int(height) / 9 * 16 / 10):  # 允许个位数的精度差异
            return heights[height]
        else:
            return str(width) + "x" + str(height)
    else:
        return str(width) + "x" + str(height)


def trans_media_file_to_hevc(json_info, file_full_path):
    """
    对输入信息的影片进行判断，如果非h265的编码格式则需要进行转码。
    并对名称进行统一管理
    [x][5][.3/29/720p]
    [x][5][.3/29/707*488]
    [分级评价][编码类型][码率/帧速/分辨率]
    分级评价：M/N/X
    编码类型：4 = h264， 5 = h265， 1 = 其他所有
    码率： 单位是MB .3 代表0.3MB = 308k， 大于9MB只显示9， 小于100K也只显示.1
    帧速: 两位数，大于99显示规则a=100，b=200,c=300依此类推，第二位数字显示帧率的十位数，因为大于100帧一般各位都为零
         如：120帧 = a2, 240帧 = b4
    分辨率： 属于正常影视宽屏16：9分辨率的仅显示纵码率加字母p，非标准则用*连接横向和纵向两个值
            如：1080p = 1920*1080， 768p = 1366*768, 720p = 1280*720, 480p = 704*480
            如：超高分辨率 4K = 3840*2160, 2K = 2560*1440

    :param json_info: 影片信息json结构体
    :param file_full_path: 影片的全局路径名称
    :return:
    """
    if not os.path.isfile(file_full_path):  # 判断文件存在
        return
    if 1 == json_info["streams"].__len__() != 1:
        log_to_file("stream number is not 1!! size:" + str(json_info["stream"].__len__()))
        return
    stream_info = json_info["streams"][0]
    format_info = json_info["format"]

    name = os.path.basename(file_full_path)
    file_path = os.path.dirname(file_full_path)
    new_name = name
    # 判断文件名是否符合规则，非规则名称记录需修改标记
    match_result = re.match(r"\[[MNX]\]\[[1|4|5]\]\[", name)
    need_change_name = 0
    if match_result is None:
        need_change_name = 1
    # 获得新的码率
    bit_rate = get_bit_rate(format_info["bit_rate"])
    if "avg_frame_rate" in stream_info:
        fps_str = get_fps_name_strs(stream_info["avg_frame_rate"], stream_info["r_frame_rate"])
    else:
        fps_str = get_fps_name_str(stream_info["nb_frames"], stream_info["duration"])
    if need_change_name is 1:
        name_part_bit_rate = get_bit_rate_name_str(bit_rate)
        name_part_width_height = get_width_height_name_str(stream_info["width"], stream_info["height"])

        new_name = "[X][5][" + name_part_bit_rate + "-" + fps_str + "-" + name_part_width_height + "]" + name
    # new_name = new_name.replace(" ", "_")
    new_name = file_path + os.path.sep + new_name
    if stream_info["codec_name"] != "hevc":

        param = command_ffmpeg_trans % (file_full_path, int(float(fps_str)), bit_rate, bit_rate, bit_rate, new_name)
        if os.path.exists(new_name):
            json_info['src_path'] = file_full_path
            json_info['des_path'] = new_name
            return
        command = command_ffmpeg + param
        begin_time = datetime.datetime.now()
        with os.popen(command) as p:
            print(p.read())
        end_time = datetime.datetime.now()
        # 需要记录的信息 1. 转前路径 2. 转后路径 3.转前大小 4.转后大小 5.转换过程时长 6.影片时长 7.转换后帧速 8.转换后码率
        before_size = round(int(format_info['size'])/1024/1024, 2)
        after_size = round(os.path.getsize(new_name)/1024/1024, 2)
        offset_size = round(before_size - after_size, 2)
        record = file_full_path + "\n" + new_name + "\n" + str(before_size) + "MB -> "
        record += str(after_size) + "MB less:" + str(offset_size) + "MB"
        record += " time:" + format_info['duration'] + " fps:" + fps_str + " rate:" + str(bit_rate)
        record += "\ntime:" + begin_time.strftime("%Y-%m-%d %H:%M:%S") + " - " \
                  + end_time.strftime("%Y-%m-%d %H:%M:%S") + "(" + str(end_time - begin_time) + ")"
        json_info = json.loads("{}")
        json_info['src_path'] = file_full_path
        json_info['des_path'] = new_name
        json_info['before_size'] = before_size
        json_info['after_size'] = after_size
        json_info['diff_size'] = offset_size
        json_info['trans_begin'] = begin_time.strftime("%Y-%m-%d %H:%M:%S")
        json_info['trans_end'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
        json_info['trans_cost'] = end_time - begin_time
        json_info['before_fps'] = int(fps_str)
        json_info['fps'] = int(fps_str)
        json_info['before_rate'] = int(format_info["bit_rate"])
        json_info['rate'] = bit_rate
        json_info['duration'] = format_info['duration']
        record_trans_result(json_info)
        print(record)
        return json_info


def trans_oper(file_name):
    info = parse_media_codec_info(file_name)
    if info.__len__() == 0:
        os.remove(file_name)
        return
    json_info = trans_media_file_to_hevc(info, file_name)
    if json_info is None:
        return
    if "before_size" in json_info:
        if json_info['before_size'] > json_info['after_size']:
            os.remove(json_info['src_path'])
        else:
            print(json_info['src_path'], ',before size:', json_info['before_size'], 'after size:', json_info['after_size'])
    # 加入等待输入，无输入超时机制


    # print(info)


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def scan_all_file(path):
    file_lst = []
    for file_path, sub_dirs, filenames in os.walk(path):
        if filenames:
            # 如果是文件，则加append到list中
            for filename in filenames:
                file = os.path.join(file_path, filename)
                print(file)
                if "ssyy" in file:
                    continue
                trans_oper(file)
                inputchar = getInput(3)
                if "q" == inputchar:
                    return
                #file_lst.append(os.path.join(file_path, filename))
        for sub_dir in sub_dirs:
            # 如果是目录，则递归调用该函数
            scan_all_file(sub_dir)
    for file_lst_item in file_lst:
        print
        file_lst_item


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    print(get_fps_name_str(180, 1))
    json_info = json.loads("{}")
    json_info["test_item"] = "1234"
    record_trans_result(json_info)
    scan_all_file(r"\\192.168.10.191\share\MyFiles\mov")
    # trans_oper(r"E:\09 讲师目录\2020-06-21 102438.mp4")
    # file_name2 = r"E:\09 讲师目录\[M][4][]模版视频.mp4"
    # trans_oper(file_name2)
    # print(info)





# See PyCharm help at https://www.jetbrains.com/help/pycharm/
