"""
    fit(X, y; loss, regularizer)

Calculate fitted w to (X, y).

# Arguments
- w::Vector{Float64}
- X::Array{Float64, 2}
- y::Vector{Float64}
- loss::LossFunction = SquaredError()
- regularizer::Union{Nothing, Regularizer} = nothing

# Returns
- Vector{Float64}: w
"""
function fit(
    X::Array{Float64, 2},
    y::Vector{Float64};
    loss::LossFunction = SquaredError(),
    regularizer::Union{Nothing, Regularizer} = nothing,
)::Vector{Float64}
    w = Vector{Float64}(undef, size(X, 2))
    fit!(w, X, y, loss, regularizer)
    w
end