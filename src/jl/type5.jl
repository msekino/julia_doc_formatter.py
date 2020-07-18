"""
    optimize(bins_::Vector{EBBBin}, maxnumbin::Int; mergegainoffset::Float64 = 14.0)::Vector{EBBBin}

binsを最大Bin数maxnumbinの下で最適化
"""
function optimize(
    bins::Vector{EBBBin},
    maxnumbin::Int;
    mergegainoffset::Float64 = 14.0,
)::Vector{EBBBin}
    binset = SortedSet{EBBBin}(bins, Reverse)

    while true
        # ゲインが最大のBinを参照
        bin = first(binset)

        # 次のBinが無いか、maxnumbin以下でゲインにオフセットを足しても0.0以下であれば終了
        (
            (bin.next === nothing) ||
            (bin.gain + mergegainoffset <= 0.0 && length(binset) <= maxnumbin)
        ) && break

        # SortedSetからbin, bin.nextを除き、マージしてSortedSetに入れ直す
        delete!(binset, bin)
        delete!(binset, bin.next)
        merge!(bin)
        push!(binset, bin)

        # bin.prevがあればbin.prevを取り出し、ゲインを更新してSortedSetに入れ直す
        if bin.prev !== nothing
            delete!(binset, bin.prev)
            updategain!(bin.prev)
            push!(binset, bin.prev)
        end
    end

    sort!(collect(binset), by = bin -> bin.xleft)
end