import configparser
import os

_cur_path = os.path.dirname(os.path.realpath(__file__))
_cfg_path = os.path.join(_cur_path, "cfg.ini")

# 创建管理对象
_conf = configparser.ConfigParser()
_conf.read(_cfg_path, encoding="utf-8")

# 保留位比特位数（默认1位）
signBits = _conf.getint('snowflake', 'signBits', fallback=1)
# 时间戳比特位数（默认41位，支持70年的毫秒值）
timestampBits = _conf.getint('snowflake', 'timestampBits', fallback=41)
# 工作机器比特位数（默认10位，支持1023台机器）
instanceBits = _conf.getint('snowflake', 'instanceBits', fallback=10)
# 序列比特位数（默认12位，单机每毫秒可以产生4095个序列）
sequenceBits = _conf.getint('snowflake', 'sequenceBits', fallback=12)
# 发号器起始时间纪元
timestampEpoch = _conf.getint('snowflake', 'timestampEpoch', fallback=0)
# 实例id（必须指定值，范围0~1023）
instanceId = _conf.getint('snowflake', 'instanceId')

if sequenceBits <= 0:
    raise Exception('sequence bits should more than 0');
if instanceBits <= 0:
    raise Exception('instance bits should more than 0');
if timestampBits <= 0:
    raise Exception('timestamp bits should more than 0');
if signBits <= 0:
    raise Exception('sign bits should more than 0');
if instanceId < 0 or instanceId >= 2 ^ instanceBits:
    raise Exception('instance id should not less than 0 and less than 2^instanceBits')
if timestampBits < 0:
    raise Exception('timestamp epoch bits should not less than 0')
if sequenceBits + instanceBits + timestampBits + signBits != 64:
    raise Exception('all bits should be 64')
