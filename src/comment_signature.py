import re
import sys


def write_signature(text):
    lines = re.split('\n', text)

    ptr_base = 0
    while ptr_base < len(lines):
        # コメント開始の検知
        if re.match('^"""\s*', lines[ptr_base]) is None:
            ptr_base += 1
            continue
        # コメント終了まで先読み
        ptr_ahead = ptr_base + 1
        while re.match('^"""\s*', lines[ptr_ahead]) is None:
            ptr_ahead += 1
        # 関数開始の検知
        regex = '^\s*function\s+'
        if re.match(regex, lines[ptr_ahead + 1]) is None:
            ptr_base = ptr_ahead
            continue
        # 関数シグネチャの抽出
        ptr_ahead += 1
        line_head = re.sub(regex, '', lines[ptr_ahead])
        func_body = ""
        for i in range(0, len(line_head)):
            c = line_head[i]
            func_body += c
            if c == '(':
                break
        stack = 1
        line_body = line_head[i+1:]
        while not stack == 0:
            for c in line_body:
                func_body += c
                if c == '(':
                    stack += 1
                if c == ')':
                    stack -= 1
            func_body += ' '
            ptr_ahead += 1
            line_body = lines[ptr_ahead]
        m = re.match('^::.+', line_body)
        if m is not None:
            func_body += m[0]
        func_body_flat = re.sub('\s+', ' ', func_body).rstrip()
        # 関数シグネチャの埋め込み
        signature = (' ' * 4) + func_body_flat
        if re.match('^\s+', lines[ptr_base + 1]) is None:
            lines[ptr_base] += ('\n' + signature + '\n')
        else:
            lines[ptr_base + 1] = signature

        ptr_base = ptr_ahead

    return '\n'.join(lines)


def main():
    file = sys.argv[1]
    with open(file, encoding='utf-8') as f:
        text = write_signature(f.read())
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)


if __name__ == '__main__':
    main()
