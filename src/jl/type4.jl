"""
    discretize(x, y, dist; maxnumbin, discretizemult = 10000.0, mergegainoffset = 14.0)

EBBによるBin分けを出力

# Arguments
- discretizemult:Float64 = 10000.0: 説明変数の離散化時に掛ける係数
- mergegainoffset:Float64 = 14.0: マージしやすさを調整するハイパーパラメータ
- x::Vector{Tx}: 説明変数ベクトル
- maxnumbin:Int = typemax(Int): 最大Bin数

# Returns
- (thresholds, expectedvalues)::Tuple{Vector{Float64}, Vector{Float64}}
  - thresholds::Vector{Float64}: EBBを学習して求めた閾値の配列
  - expectedvalues::Vector{Float64}: 各Binの目的変数期待値の配列
"""
function discretize(
    x::Vector{Tx},
    y::Vector{Ty},
    dist::Distribution;
    maxnumbin::Int = typemax(Int),
    discretizemult::Float64 = 10000.0,
    mergegainoffset::Float64 = 14.0,
)::Tuple{Vector{Float64}, Vector{Float64}} where {Tx, Ty}
