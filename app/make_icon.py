# 앱 아이콘(icon.ico)을 만든다. 화면 왼쪽 위 로고와 같은 모양: 연한 파랑 둥근 사각형 + 파랑 링크 기호.
# 아이콘을 바꿀 때만 실행한다: .venv\Scripts\python.exe make_icon.py  (Pillow 필요, requirements-build.txt)
from pathlib import Path

from PIL import Image, ImageDraw

from ui import C

BIG = 1024
SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]


def rgb(hex_color):
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def draw_logo(symbol=20 / 36, stroke=1.15, border=True):
    img = Image.new('RGBA', (BIG, BIG), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 로고(36px, 반지름 10px)를 아이콘 전체로 키운다. 테두리는 밝은 바탕에서도 모양이 보이게 한다
    d.rounded_rectangle((0, 0, BIG - 1, BIG - 1), radius=BIG * 10 // 36, fill=rgb(C['primary-soft']),
                        outline=rgb('#C7D7FE') if border else None, width=BIG // 48 if border else 0)
    # 링크 기호는 24 단위 좌표, 로고 안에서 symbol 비율 크기로 가운데에 둔다
    k = BIG * symbol / 24
    o = (BIG - 24 * k) / 2
    w = round(2.2 * k * stroke)
    blue = rgb(C['primary'])

    def pt(x, y):
        return o + x * k, o + y * k

    def cap(x, y):
        cx, cy = pt(x, y)
        d.ellipse((cx - w / 2, cy - w / 2, cx + w / 2, cy + w / 2), fill=blue)

    for (x1, y1, x2, y2) in ((7, 7, 9, 7), (7, 17, 9, 17), (15, 7, 17, 7), (15, 17, 17, 17), (8, 12, 16, 12)):
        d.line((*pt(x1, y1), *pt(x2, y2)), fill=blue, width=w)
        cap(x1, y1)
        cap(x2, y2)
    # 왼쪽 반원(중심 7,12)과 오른쪽 반원(중심 17,12), 반지름 5
    for cx, start, end in ((7, 90, 270), (17, -90, 90)):
        d.arc((*pt(cx - 5 - 0.0, 7), *pt(cx + 5, 17)), start=start, end=end, fill=blue, width=w)
    return img


def main():
    # 32px 이하(작업 표시줄, 탐색기 작은 아이콘)는 기호를 키우고 굵게, 테두리 없이 그려야 알아볼 수 있다
    small, large = draw_logo(symbol=0.8, stroke=1.5, border=False), draw_logo()
    frames = [(small if s <= 32 else large).resize((s, s), Image.LANCZOS) for s in SIZES]
    out = Path(__file__).resolve().parent / 'icon.ico'
    frames[-1].save(out, sizes=[(s, s) for s in SIZES], append_images=frames[:-1])
    print(f'{out} ({", ".join(map(str, SIZES))})')


if __name__ == '__main__':
    main()
