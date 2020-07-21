import re
import sys


def format_comments(text, thres_len = 92):
    lines_orig = re.split('\n', text)
    lines_edited = []

    iline_comment_head = -1
    iline_comment_tail = -1  
    iline = 0

    while iline < len(lines_orig):
        # Detect the first line of a function
        line = lines_orig[iline]
        isfunc = \
            iline_comment_tail > -1 or \
            re.match('^\s*function', line) is not None or \
            re.match('^\S+\(', line) is not None

        if isfunc:
            signature, arg_names, arg_types, kwarg_names, kwarg_types, return_types \
                = extract_signature(lines_orig, iline)

            signature, contains_type \
                = shorten_signature(signature, arg_types, kwarg_types, thres_len)

            comment_lines = make_comment_lines(
                signature,
                # If the signature contains types, the comment don't contain the types.
                not contains_type,
                arg_names,
                arg_types,
                kwarg_names,
                kwarg_types,
                return_types,
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

            # Detect the first line of a comment
            if re.match('^"""\s*', lines_orig[iline]) is None:
                lines_edited.append(line)
                iline += 1
                continue

            iline_comment_head = iline
            iline += 1

            # Proceed to the end of the comment
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
                    return_types = extract_return_types(line[i+1:])
                    break             
        if stack == 0:
            break
        iline += 1
        line = re.sub('^\s+', '' if line[len(line)-1] == '(' else ' ', lines[iline])

    if signature[len(signature)-2:] == ',)':
        signature = signature[:len(signature)-2] + ')'

    arg_names, arg_types, kwarg_names, kwarg_types = extract_arguments(signature)
    
    return signature, arg_names, arg_types, kwarg_names, kwarg_types, return_types


def extract_return_types(line):
    return_types = []
    
    if line[0:len('::')] == '::':
        # Ignore outermost 'Tuple'
        line = line[len('::Tuple{'):] \
            if line[0:len('::Tuple{')] == '::Tuple{' \
            else line[len('::'):]
        
        return_type = ''
        stack = 0

        for c in line:
            if stack == 0 and c == '}':
                break
            
            if stack == 0 and len(return_type) > 0 and c in {',', ' ', '='}:
                return_types.append(return_type)
                return_type = ''
                continue
                
            if len(return_type) > 0 or c not in {',', ' ', '='}:
                return_type += c
              
            if c == '{':
                stack += 1
            if c == '}':
                stack -= 1
        
        if len(return_type) > 0:
            return_types.append(return_type)
    
    return return_types


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


def shorten_signature(signature, arg_types, kwarg_types, thres_len):
    contains_type = True

    if len(signature) <= thres_len:
        return signature, contains_type

    # Remove types
    contains_type = False
        
    for arg_name, arg_type in arg_types.items():
        if '=' in arg_type:
            if ', '+ arg_name in signature:
                signature = signature.replace(', '+ arg_name +'::'+ arg_type, '[, '+ arg_name +']')
            else:
                signature = signature.replace(arg_name +'::'+ arg_type, '['+ arg_name +']')
        else:
            signature = signature.replace('::'+ arg_type, '')

    for arg_name, arg_type in kwarg_types.items():
        if '=' in arg_type:
            if '; '+ arg_name in signature:
                signature = signature.replace('; '+ arg_name +'::'+ arg_type, '[; '+ arg_name +']')
            else:
                signature = signature.replace(', '+ arg_name +'::'+ arg_type, '[, '+ arg_name +']')
        else:
            signature = signature.replace('::'+ arg_type, '')

    # Replace keywords arguments with '<keyword arguments>', if it's going to be short.
    kwarg_names = kwarg_types.keys()        
    if len(signature) <= thres_len or len(', '.join(kwarg_names)) < len('<keyword arguments>'):
        return signature, contains_type

    return signature[0:signature.find(';')] + '; <keyword arguments>)', contains_type


def make_comment_lines(signature, contains_type, arg_names, arg_types, kwarg_names, kwarg_types, return_types, lines_orig, iline_comment_head, iline_comment_tail):
    arg_comments = {} if iline_comment_head == -1 \
        else extract_arg_comments(lines_orig, iline_comment_head, iline_comment_tail, arg_names, kwarg_names)

    comment_lines = []
    comment_lines.append('\"\"\"')
    comment_lines.append((' ' * 4) + signature)

    is_signature_line = True

    for iline in range(iline_comment_head + 1, iline_comment_tail):
        line = lines_orig[iline]

        if re.match('^# Arguments', line) is not None:
            break

        if re.match('\s+', line) is None:
            is_signature_line = False

        if not is_signature_line:
            comment_lines.append(line)

    # Insert an empty line before '# Arguments' line.
    if comment_lines[len(comment_lines)-1] != '':
        comment_lines.append('')

    comment_lines.append('# Arguments')
    
    for arg_name in arg_names:
        comment = arg_comments[arg_name] if arg_name in arg_comments else ' '

        arg_type = arg_types[arg_name]
        if contains_type:
            comment_lines.append('- `'+ arg_name +'::'+ arg_type +'`:'+ comment)
        else:
            comment_lines.append('- '+ arg_name +':'+ comment)
            
    for arg_name in kwarg_names:
        comment = arg_comments[arg_name] if arg_name in arg_comments else ' '
        
        arg_type = kwarg_types[arg_name]
        if contains_type:
            comment_lines.append('- `; '+ arg_name +'::'+ arg_type +'`:'+ comment)
        else:
            comment_lines.append('- ; '+ arg_name +':'+ comment)
    
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

    if not return_comment_added and len(return_types) > 0:
        comment_lines.append('')
        comment_lines.append('# Returns')
        for return_type in return_types:
            comment_lines.append('- '+ return_type +': ')
        
    comment_lines.append('\"\"\"')
    return comment_lines


def extract_arg_comments(lines_orig, iline_comment_head, iline_comment_tail, arg_names, kwarg_names):
    arg_comments = {}

    for iline in range(iline_comment_head + 1, iline_comment_tail):
        line = lines_orig[iline]
            
        if re.match('^-\s', line) is None:
            continue
        
        for arg_name in arg_names:
            if re.match('^-\s`?'+ arg_name +':', line):
                i1 = line.rfind('::')
                i2 = line.rfind(':')                
                if i2 > i1 + 1:
                    arg_comments[arg_name] = line[line.rfind(':') + 1:]
                break

        for arg_name in kwarg_names:
            if re.match('^-\s`?(; )?'+ arg_name +':', line):
                i1 = line.rfind('::')
                i2 = line.rfind(':')                
                if i2 > i1 + 1:
                    arg_comments[arg_name] = line[line.rfind(':') + 1:]
                break

    return arg_comments


def main():
    file = sys.argv[1]
    thres_len = int(sys.argv[2]) if len(sys.argv) >= 3 else 92
    
    with open(file, encoding='utf-8') as f:
        text = format_comments(f.read(), thres_len)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)


if __name__ == '__main__':
    main()
