# Galaxy Connect for ARM64 데스크톱 앱 진입점.
#   python main.py                 실제 스크립트로 실행
#   python main.py --mock [--lang en] [--consent]   가짜 데이터로 화면만 확인 (개발용)
import argparse

import ui


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mock', action='store_true')
    parser.add_argument('--lang', choices=['ko', 'en'])
    parser.add_argument('--consent', action='store_true', help='--mock 에서 동의 창부터 보기')
    args = parser.parse_args()
    if args.mock:
        import mock as backend
        if args.lang:
            backend.SETTINGS['lang'] = args.lang
        if args.consent:
            backend.SETTINGS['consented'] = False
    else:
        import backend
    ui.run(backend)


if __name__ == '__main__':
    main()
