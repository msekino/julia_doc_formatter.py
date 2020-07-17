



Base.:isless(bin1::EBBBin, bin2::EBBBin)::Bool =
    (bin2.gain != bin1.gain) ? bin1.gain < bin2.gain : bin1.xleft < bin2.xleft