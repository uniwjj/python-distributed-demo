from idgenerator import config
import threading
import time


class SnowflakeIdGenerator:
    current_sequence = None

    def __init__(self, cfg: config):
        self.timestamp_epoch = cfg.timestampEpoch
        self.instance_id = cfg.instanceId
        self.sequence_bits = cfg.sequenceBits
        self.instance_bits = cfg.instanceBits
        self.instance_shift = self.sequence_bits
        self.timestamp_shift = self.sequence_bits + self.instance_bits
        self.sequence_mask = ~(-1 << self.sequence_bits)

    def __sequence(self, value: int, timestamp: int):
        """
        获取序列对象
        :param value: 序列值
        :param timestamp: 毫秒时间戳
        :return: 序列对象
        :rtype: Sequence
        """
        outer = self

        class Sequence:
            def __init__(self, value: int, timestamp: int):
                self.value = value
                self.timestamp = timestamp

            def get_id(self) -> int:
                """
                获取序列id
                :return: 序列id
                """
                return ((self.timestamp - outer.timestamp_epoch) << outer.timestamp_shift) \
                       | (outer.instance_id << outer.instance_shift) \
                       | self.value

        return Sequence(value, timestamp)

    def wait_next_timestamp(self, timestamp: int) -> int:
        """
        等待下一个毫秒时间戳
        :type timestamp: 当前毫秒时间戳
        :return: 下一个毫秒时间戳
        :rtype int
        """
        now = self.get_timestamp(time.time())
        while now == timestamp:
            time.sleep(0.001)
            now = self.get_timestamp(time.time())
        return now

    @staticmethod
    def get_timestamp(time: float) -> int:
        """
        获取毫秒级时间戳
        :param time: 时间
        :return: 毫秒级时间戳
        :rtype: int
        """
        return int(round(time * 1000))

    def next_id(self) -> int:
        """
        获取下一个id
        :return: 下一个id
        :rtype: int
        """
        lock = threading.Lock()
        try:
            # 阻塞形式获取锁，10秒自动超时
            if not lock.acquire(blocking=True, timeout=10):
                return None

            next_sequence = None
            current_timestamp = self.get_timestamp(time.time())
            if self.current_sequence is None or self.current_sequence.timestamp < current_timestamp:
                next_sequence = self.__sequence(0, current_timestamp)
            elif self.current_sequence.timestamp == current_timestamp:
                next_value = self.current_sequence.value + 1 & self.sequence_mask
                if next_value == 0:
                    current_timestamp = self.wait_next_timestamp()
                next_sequence = self.__sequence(next_value, current_timestamp)
            else:
                raise Exception('clock moves backward')
            self.current_sequence = next_sequence
            return self.current_sequence.get_id()
        finally:
            if lock.locked():
                lock.release()

    @staticmethod
    def get_char(num: int) -> chr:
        if num <= 9:
            return chr(num + ord('0'))
        return chr(num - 10 + ord('A'))

    def next_str(self) -> str:
        next_id = self.next_id()
        chars = ['0' for i in range(13)]
        for i in range(13):
            c = self.get_char(int(next_id & 0x1f))
            chars[12-i] = c
            next_id = next_id >> 5
        return ''.join(chars)


if __name__ == '__main__':
    class GeneratorThread(threading.Thread):
        def __init__(self, name: str, generator: SnowflakeIdGenerator):
            threading.Thread.__init__(self)
            self.name = name
            self.generator = generator

        def run(self) -> None:
            for i in range(100):
                print(self.name + ': ' + self.generator.next_str())
                time.sleep(0.1)

    id_generator = SnowflakeIdGenerator(config)
    threads = list()
    for i in range(10):
        threads.append(GeneratorThread(name='thread-' + str(i), generator=id_generator))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
