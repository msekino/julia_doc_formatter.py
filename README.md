# julia_doc_formatter.py
## Files
```
<root>
├── src
│   └── julia_doc_formatter.py         Julia Doc Formatter
├── vsix
│   └── script-applier-0.0.1.vsix      Script Applier (VSCode Extension)
└── README.md
```

## Examples
### Function definition with basic syntax
When the formatter find "function", the formatted docstring will be added.
```
> cat "D:\example.jl"
function f(x::Vector{Tx}, y::Vector{Ty})::Float64 where {Tx, Ty}
end

> python julia_doc_formatter.py "D:\example.jl"

> cat "D:\example.jl"
"""
    f(x::Vector{Tx}, y::Vector{Ty})

# Arguments
- x: 
- y: 

# Returns
- Float64: 
"""
function f(x::Vector{Tx}, y::Vector{Ty})::Float64 where {Tx, Ty}
end
```
When including the types in the function signature results in longer than 'thres_len = 92', the types will not be included in the signature.
```
> cat "D:\example.jl"
function f(
    argument1::Vector{T1},
    argument2::Vector{T2},
    argument3::Vector{T3},
    argument4::Vector{T4},
)::Float64 where {T1, T2, T3, T4}
end

> python julia_doc_formatter.py "D:\example.jl"

> cat "D:\example.jl"
"""
    f(argument1, argument2, argument3, argument4)

# Arguments
- `argument1::Vector{T1}`: 
- `argument2::Vector{T2}`: 
- `argument3::Vector{T3}`: 
- `argument4::Vector{T4}`: 

# Returns
- Float64: 
"""
function f(
    argument1::Vector{T1},
    argument2::Vector{T2},
    argument3::Vector{T3},
    argument4::Vector{T4},
)::Float64 where {T1, T2, T3, T4}
end
```
When including the keyword arguments in the function signature results in longer than 'thres_len = 92', rewrite the keyword arguments together to "\<keyword arguments\>".
```
> cat "D:\example.jl"
function f(
    argument1::Vector{T1},
    argument2::Vector{T2},
    argument3::Vector{T3},
    argument4::Vector{T4};
    kargument1,
    kargument2,
    kargument3,
    kargument4
)::Float64 where {T1, T2, T3, T4}
end

> python julia_doc_formatter.py "D:\example.jl"

> cat "D:\example.jl"
"""
    f(argument1, argument2, argument3, argument4; <keyword arguments>)

# Arguments
- `argument1::Vector{T1}`: 
- `argument2::Vector{T2}`: 
- `argument3::Vector{T3}`: 
- `argument4::Vector{T4}`: 
- `; kargument1`: 
- `; kargument2`: 
- `; kargument3`: 
- `; kargument4`: 

# Returns
- Float64: 
"""
function f(
    argument1::Vector{T1},
    argument2::Vector{T2},
    argument3::Vector{T3},
    argument4::Vector{T4};
    kargument1,
    kargument2,
    kargument3,
    kargument4
)::Float64 where {T1, T2, T3, T4}
end
```

### Assignment form
A formatted docstring will be added to the assignment form function only if it can be detected.
```
> cat "D:\example.jl"
f(x) = x * y

> python julia_doc_formatter.py "D:\example.jl"

> cat "D:\example.jl"
"""
    f(x)

# Arguments
- x:
"""
f(x) = x * y
```

## Script Applier (VSCode Extension)
Script Applier (script-applier-0.0.1.vsix) is a VSCode extension that applies a script to the selected lines or file being edited.
`Ctrl+Shift+D` is the shortcut key for applying the script.

### Installation
You can install script-applier-0.0.1.vsix using the Install from VSIX command in the Extensions view command drop-down.
https://code.visualstudio.com/docs/editor/extension-gallery#_install-from-a-vsix

### Setting for applying the julia_doc_formatter.py
Please add the following to VSCode's settings.json.
```
"script-applier.command": "python [PATH]/julia_doc_formatter.py %TARGET"
```