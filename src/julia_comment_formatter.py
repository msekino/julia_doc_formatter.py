import re
import sys


def format_comments(text, lenthres = 80):
    lines_orig = re.split('\n', text)
    lines_edited = []

    iline_comment_head = -1
    iline_comment_tail = -1  
    iline = 0

    while iline < len(lines_orig):
        # 関数の検知
        line = lines_orig[iline]
        isfunc = \
            re.match('^\s*function', line) is not None or \
            re.match('^\S+\(', line) is not None

        print(f"{iline}, {isfunc}, {iline_comment_head}, {iline_comment_tail}")

        if isfunc:
            signature, arg_names, arg_types, kwarg_names, kwarg_types, return_type \
                = extract_signature(lines_orig, iline)

            signature, contains_type \
                = shorten_signature(signature, arg_types, kwarg_types, return_type, lenthres)

            comment_lines = make_comment_lines(
                signature,
                not contains_type,  # signatureにtypeが含まれたら、commentには記載しない
                arg_names,
                arg_types,
                kwarg_names,
                kwarg_types,
                return_type,
                lines_orig,
                iline_comment_head,
                iline_comment_tail
            )

            lines_edited += comment_lines
            lines_edited.append(line)

            iline_comment_head = -1
            iline_comment_tail = -1
            iline += 1
        else:
            iline_comment_head = -1
            iline_comment_tail = -1

            # コメント開始の検知
            if re.match('^"""\s*', lines_orig[iline]) is None:
                lines_edited.append(line)
                iline += 1
                continue

            iline_comment_head = iline
            iline += 1

            # コメント終了まで先読み
            while re.match('^"""\s*', lines_orig[iline]) is None:
                iline += 1

            iline_comment_tail = iline
            iline += 1
    
    return '\n'.join(lines_edited)
    

def extract_signature(lines, iline):
    line = lines[iline]
    line = re.sub('^\s*function\s+', '', line)

    signature = ''
    return_type = ''
    stack = 0
       
    while True:
        for i in range(0, len(line)):
            c = line[i]
            signature += c
            if c == '(':
                stack += 1
            if c == ')':
                stack -= 1
                if stack == 0:
                    return_type = extract_return_type(line[i+1:])
                    break             
                    
        if stack == 0:
            break
            
        iline += 1
        line = re.sub('^\s+', '' if line[len(line)-1:] == '(' else ' ', lines[iline])

    if signature[len(signature)-2:] == ',)':
        signature = signature[:len(signature)-2] + ')'

    if len(return_type) > 0:
        signature += '::'+ return_type
        
    arg_names, arg_types, kwarg_names, kwarg_types = extract_arguments(signature)
    
    return signature, arg_names, arg_types, kwarg_names, kwarg_types, return_type


def extract_return_type(line):
    if line[0:2] == '::':
        return_type = ''
        stack = 0
        
        for i in range(2, len(line)):
            c = line[i]
            if stack == 0 and c in {' ', '='}:
                break
                
            return_type += c
            
            if c == '{':
                stack += 1
            if c == '}':
                stack -= 1
                if stack == 0:
                    break
        
        return return_type
    else:
        return ''


def extract_arguments(signature):
    body = signature[signature.find('(') + 1:signature.rfind(')')]

    arg_names = []
    arg_types = {}
    kwarg_names = []
    kwarg_types = {}
    
    arg_name = ''
    arg_type = ''
    has_colon = False
    has_semicolon = False
    stack = 0
    
    for c in body:
        if len(arg_name) == 0 and c == ' ':
            continue
        elif c == ':':
            has_colon = True
        elif c == ';':
            arg_names.append(arg_name)
            arg_types[arg_name] = arg_type
            arg_name = ''
            arg_type = ''
            has_colon = False
            has_semicolon = True
        elif c in {'(', '{'}:
            arg_type += c
            stack += 1
        elif c in {')', '}'}:
            arg_type += c
            stack -= 1
        elif stack == 0 and c == ',':
            if has_semicolon:
                kwarg_names.append(arg_name)
                kwarg_types[arg_name] = arg_type
            else:
                arg_names.append(arg_name)
                arg_types[arg_name] = arg_type                
            arg_name = ''            
            arg_type = ''
            has_colon = False
        elif has_colon:
            arg_type += c
        else:
            arg_name += c

    if has_semicolon:
        kwarg_names.append(arg_name)
        kwarg_types[arg_name] = arg_type
    else:
        arg_names.append(arg_name)
        arg_types[arg_name] = arg_type
    
    return arg_names, arg_types, kwarg_names, kwarg_types


def shorten_signature(signature, arg_types, kwarg_types, return_type, lenthres):
    contains_type = True

    if len(signature) <= lenthres:
        return signature, contains_type

    for arg_type in arg_types.values():
        signature = signature.replace('::'+ arg_type, '')

    for arg_type in kwarg_types.values():
        signature = signature.replace('::'+ arg_type, '')

    contains_type = False

    if len(signature) <= lenthres:
        return signature, contains_type

    return signature[0:signature.find(';')] + '; <keyword arguments>)::'+ return_type, contains_type


def make_comment_lines(signature, contains_type, arg_names, arg_types, kwarg_names, kwarg_types, return_type, lines_orig, iline_comment_head, iline_comment_tail):
    arg_comments = {} if iline_comment_head == -1 \
        else extract_arg_comments(lines_orig, iline_comment_head, iline_comment_tail, arg_names, kwarg_names)

    comment_lines = []
    comment_lines.append('\"\"\"')
    comment_lines.append((' ' * 4) + signature)

    for iline in range(iline_comment_head + 1, iline_comment_tail):
        line = lines_orig[iline]
        
        if re.match('^# Arguments', line) is not None:
            break
           
        if re.match('\s+', line) is None:
            comment_lines.append(line)

    comment_lines.append("")
    comment_lines.append("# Arguments")
    
    for arg_name in arg_names:
        comment = arg_comments[arg_name] if arg_name in arg_comments else ' '

        arg_type = arg_types[arg_name]
        if contains_type:
            comment_lines.append("- `"+ arg_name +"::"+ arg_type +"`:"+ comment)
        else:
            comment_lines.append("- "+ arg_name +":"+ comment)
            
    for arg_name in kwarg_names:
        comment = arg_comments[arg_name] if arg_name in arg_comments else ' '
        
        arg_type = kwarg_types[arg_name]
        if contains_type:
            comment_lines.append("- `; "+ arg_name +"::"+ arg_type +"`:"+ comment)
        else:
            comment_lines.append("- ; "+ arg_name +":"+ comment)
    
    return_comment_added = False

    for iline in range(iline_comment_head + 1, iline_comment_tail):
        line = lines_orig[iline]
        if re.match('^# Returns', line) is None:
            continue

        comment_lines.append('')       
        for iline2 in range(iline, iline_comment_tail):
            line = lines_orig[iline2]
            comment_lines.append(line)
            return_comment_added = True
        break

    if not return_comment_added and return_type != '':
        comment_lines.append('')
        comment_lines.append('# Returns')
        comment_lines.append('- ')
        
    comment_lines.append('\"\"\"')
    return comment_lines


def extract_arg_comments(lines_orig, iline_comment_head, iline_comment_tail, arg_names, kwarg_names):
    arg_comments = {}

    for iline in range(iline_comment_head + 1, iline_comment_tail):
        line = lines_orig[iline]
            
        if re.match('^-\s', line) is None:
            continue
        
        for arg_name in arg_names:
            if re.match('^-\s'+ arg_name +':', line) or re.match('^-\s`'+ arg_name +':', line):
                arg_comments[arg_name] = line[line.rfind(':') + 1:]
                break

        for arg_name in kwarg_names:
            if re.match('^-\s'+ arg_name +':', line) or re.match('^-\s`'+ arg_name +':', line):
                arg_comments[arg_name] = line[line.rfind(':') + 1:]
                break

    return arg_comments


def main():
    file = sys.argv[1]
    with open(file, encoding='utf-8') as f:
        text = format_comments(f.read())
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)


if __name__ == '__main__':
    main()
