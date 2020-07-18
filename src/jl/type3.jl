function discretize(
    x::Vector{Tx},
    y::Vector{Ty},
    dist::Distribution;
    maxnumbin::Int = typemax(Int),
    discretizemult::Float64 = 10000.0,
    mergegainoffset::Float64 = 14.0,
)::Tuple{Vector{Float64}, Vector{Float64}} where {Tx, Ty}