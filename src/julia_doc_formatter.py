import re
import sys

from collections import OrderedDict 

def format_docs(text, thres_len = 92):
    lines_orig = re.split('\n', text)
    lines_edited = []

    iline_doc_head = -1
    iline_doc_tail = -1  
    iline = 0

    while iline < len(lines_orig):
        # Detect the first line of a function
        line = lines_orig[iline]
        isfunc = \
            iline_doc_tail > -1 or \
            re.match('^\s*function', line) is not None or \
            re.match('^\S+\(', line) is not None

        if isfunc:
            if re.match('\s+', line) is not None:
                indent = line[0:re.match('\s+', line).end()]
            else:
                indent = ''
            
            signature, args, kwargs, return_types = extract_signature(lines_orig, iline)
            signature, contains_type = shorten_signature(signature, args, kwargs, thres_len)

            doc_lines = make_doc_lines(
                indent,
                signature,
                not contains_type,  # If the signature contains types, doc don't contain the types.
                args,
                kwargs,
                return_types,
                lines_orig,
                iline_doc_head,
                iline_doc_tail
            )

            lines_edited += doc_lines
            lines_edited.append(line)

            iline_doc_head = -1
            iline_doc_tail = -1
            iline += 1
        else:
            iline_doc_head = -1
            iline_doc_tail = -1

            # Detect the first line of a doc
            if re.match('^\s*"""\s*', lines_orig[iline]) is None:
                lines_edited.append(line)
                iline += 1
                continue

            iline_doc_head = iline
            iline += 1

            # Proceed to the end of the doc
            while re.match('^\s*"""\s*', lines_orig[iline]) is None:
                iline += 1

            iline_doc_tail = iline
            iline += 1
    
    return '\n'.join(lines_edited)
    

def extract_signature(lines, iline):
    line = lines[iline]
    line = re.sub('^\s*function\s+', '', line)

    signature = ''
    return_types = []
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

    args, kwargs = extract_arguments(signature)
    
    return signature, args, kwargs, return_types


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
                if c in {',', '='}:
                    continue
                else:
                    break
                
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

    args = OrderedDict()
    kwargs = OrderedDict()
    
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
            args[arg_name] = arg_type
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
                kwargs[arg_name] = arg_type
            else:
                args[arg_name] = arg_type
            arg_name = ''            
            arg_type = ''
            has_colon = False
        elif has_colon:
            arg_type += c
        else:
            arg_name += c

    if has_semicolon:
        kwargs[arg_name] = arg_type
    else:
        args[arg_name] = arg_type
    
    return args, kwargs


def shorten_signature(signature, args, kwargs, thres_len):
    contains_type = True

    if len(signature) <= thres_len:
        return signature, contains_type

    # Remove types
    contains_type = False
    
    for arg_name, arg_type in args.items():
        if '=' in arg_type:
            signature = signature.replace('::'+ arg_type[0:arg_type.find(' =')], '')
        else:
            signature = signature.replace('::'+ arg_type, '')

    for arg_name, arg_type in kwargs.items():
        if '=' in arg_type:
            signature = signature.replace('::'+ arg_type[0:arg_type.find(' =')], '')
        else:
            signature = signature.replace('::'+ arg_type, '')

    if len(signature) <= thres_len:
        return signature, contains_type

    # Replace keywords arguments with '<keyword arguments>', if it's going to be short.
    kwarg_names = kwargs.keys()        
    if len(signature) <= thres_len or len(', '.join(kwarg_names)) > len('<keyword arguments>'):
        signature = signature[0:signature.find(';')] + '; <keyword arguments>)'

    if len(signature) <= thres_len:
        return signature, contains_type

    # Remove default values
    for arg_name, arg_type in args.items():
        signature = signature.replace(arg_type[arg_type.find(' ='):], '')

    for arg_name, arg_type in kwargs.items():
        signature = signature.replace(arg_type[arg_type.find(' ='):], '')
    
    return signature, contains_type    


def make_doc_lines(indent, signature, contains_type, args, kwargs, return_types, lines_orig, iline_doc_head, iline_doc_tail):
    arg_docs = {} if iline_doc_head == -1 \
        else extract_arg_docs(lines_orig, iline_doc_head, iline_doc_tail, args, kwargs)

    doc_lines = []
    doc_lines.append(indent +'\"\"\"')
    doc_lines.append(indent +(' ' * 4) + signature)

    is_signature_line = True

    for iline in range(iline_doc_head + 1, iline_doc_tail):
        line = lines_orig[iline][len(indent):]

        if re.match('^# Arguments', line) is not None:
            break

        if re.match('\s+', line) is None:
            is_signature_line = False

        if not is_signature_line:
            doc_lines.append(indent + line)

    # Insert an empty line before '# Arguments' line.
    if re.match('^\s*\S', doc_lines[len(doc_lines)-1]) is not None:
        doc_lines.append(indent)

    doc_lines.append(indent +'# Arguments')
    
    for arg_name, arg_type in args.items():
        doc = arg_docs[arg_name] if arg_name in arg_docs else ' '

        if contains_type:
            if len(arg_type) > 0:
                doc_lines.append(indent +'- `'+ arg_name +'::'+ arg_type +'`:'+ doc)
            else:
                doc_lines.append(indent +'- `'+ arg_name +'`:'+ doc)
        else:
            doc_lines.append(indent +'- '+ arg_name +':'+ doc)
            
    for arg_name, arg_type in kwargs.items():
        doc = arg_docs[arg_name] if arg_name in arg_docs else ' '
        
        if contains_type:
            if len(arg_type) > 0:
                doc_lines.append(indent +'- `; '+ arg_name +'::'+ arg_type +'`:'+ doc)
            else:
                doc_lines.append(indent +'- `; '+ arg_name +'`:'+ doc)
        else:
            doc_lines.append(indent +'- ; '+ arg_name +':'+ doc)
    
    return_doc_added = False

    for iline in range(iline_doc_head + 1, iline_doc_tail):
        line = lines_orig[iline][len(indent):]

        if re.match('^# Returns', line) is None:
            continue

        doc_lines.append(indent)

        for iline2 in range(iline, iline_doc_tail):
            line = lines_orig[iline2][len(indent):]
            doc_lines.append(indent + line)
            return_doc_added = True
        break

    if not return_doc_added and len(return_types) > 0:
        doc_lines.append('')
        doc_lines.append(indent +'# Returns')
        for return_type in return_types:
            doc_lines.append(indent +'- '+ return_type +': ')
        
    doc_lines.append(indent +'\"\"\"')
    return doc_lines


def extract_arg_docs(lines_orig, iline_doc_head, iline_doc_tail, args, kwargs):
    arg_docs = {}

    for iline in range(iline_doc_head + 1, iline_doc_tail):
        line = lines_orig[iline]
            
        if re.match('^\s*-\s', line) is None:
            continue
        
        for arg_name in args.keys():
            if re.match('^\s*-\s`?'+ arg_name +':', line):
                i1 = line.rfind('::')
                i2 = line.rfind(':')                
                if i2 > i1 + 1:
                    arg_docs[arg_name] = line[line.rfind(':') + 1:]
                break

        for arg_name in kwargs.keys():
            if re.match('^\s*-\s`?(; )?'+ arg_name +':', line):
                i1 = line.rfind('::')
                i2 = line.rfind(':')                
                if i2 > i1 + 1:
                    arg_docs[arg_name] = line[line.rfind(':') + 1:]
                break

    return arg_docs


def main():
    file = sys.argv[1]
    thres_len = int(sys.argv[2]) if len(sys.argv) >= 3 else 92
    
    with open(file, encoding='utf-8') as f:
        text = format_docs(f.read(), thres_len)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(text)


if __name__ == '__main__':
    main()
