"""
    merge!(bin::EBBBin)

binをbin.nextとマージ
"""
function merge!(bin::EBBBin)
    # binのstatにbin.nextのstatを加算
    add!(bin.stat, bin.next.stat)

    # 境界値の更新
    bin.xright = bin.next.xright

    # 次のBinに対する参照の更新
    bin.next = bin.next.next
    (bin.next !== nothing) && (bin.next.prev = bin)

    # bin.nextとマージしたときのゲインを更新
    updategain!(bin)
end