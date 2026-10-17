# 개발용 가짜 백엔드. python main.py --mock 으로 화면만 확인한다.
# 설정 파일, 레지스트리, Galaxy Connect 는 건드리지 않는다.
import time

from backend import APP_NAME, VERSION  # noqa: F401  (ui 가 backend 와 같은 이름을 쓴다)

SETTINGS = {'consented': True}

STATUS = {
    'Registry': {'Manufacturer': 'Samsung Electronics', 'ProductName': '940XMA'},
    'AppSees': {'Manufacturer': 'Samsung Electronics', 'ProductName': '940XMA'},
    'Firmware': {'Manufacturer': 'HP', 'ProductName': 'OmniBook X Laptop 14-fe0xxx'},
    'GalaxyConnect': '4.6.1217.0',
    'MultiControl': '2.7.1300.0',
    'Service': 'Running',
    'Detection': {'Time': '2026-10-17 12:18:49.9426', 'Manufacturer': 'Samsung Electronics', 'IsSamsungDevice': True},
    'HasBackup': True,
    'Log': [
        '2026-10-17 12:10:41.1022 [INFO] [P:1 | T:1] [Service.cs::Start (20)] \tSamsung Multi Control Service started',
        '2026-10-17 12:10:54.3310 [INFO] [P:1 | T:1] [Device.cs::Info (88)] \tMCF DeviceInfo: Arm64 | Samsung Electronics | 940XMA',
        '2026-10-17 12:18:49.9426 [INFO] [P:1 | T:1] [Device.cs::Check (56)] \tIsSamsungDevice: True',
        '2026-10-17 12:18:49.9520 [INFO] [P:1 | T:1] [Ble.cs::Check (31)] \tSupport Extended BLE: Qualcomm FastConnect 7800',
    ],
}


def read_settings():
    return dict(SETTINGS)


def write_settings(patch):
    SETTINGS.update(patch)
    return dict(SETTINGS)


def get_status():
    time.sleep(0.3)
    return STATUS


def run_action(name, on_line):
    for line in ('== 1. 백업', '백업이 이미 있습니다', '== 2. 레지스트리 적용', '완료.'):
        time.sleep(0.3)
        on_line(line)
    return {'ok': True, 'cancelled': False, 'code': 0, 'error': None}
