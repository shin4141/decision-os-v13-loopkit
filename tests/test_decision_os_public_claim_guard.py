from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
from io import StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zlib

from decision_os.cli import main as cli_main
from decision_os.companion.intelligence_transplant import (
    IntelligenceTransplantController,
)
from decision_os.companion.manual_bridge import (
    build_intelligence_transplant_transport,
)
from decision_os.intelligence_transplant import (
    AUDIT_COMPLETION_RECEIPT,
    AUDIT_INPUT_MANIFEST,
    E1_DISCOVERY,
    E2_AUDIT,
    E3_ACCEPTED_DISCOVERY,
    GENERALIZED_BOUNDARY,
    PUBLIC_CLAIM_MANIFEST,
    RUN_CHARTER,
    SCHEMA_VERSION,
    SEAT_ASSIGNMENT_RECEIPT,
    canonical_json,
    exact_ref,
    object_with_content_hash,
    reduce_evidence_graph,
    validate_graph,
    validate_object,
)
from decision_os.public_claim_guard import (
    ALLOW,
    ASSET_IDENTITY,
    ASSET_TYPE,
    ASSET_VERSION,
    BLOCK,
    EVIDENCE_APPLICABILITY_MISMATCH,
    EVALUATION_SCHEMA_VERSION,
    HOLD,
    MANIFEST_TRANSPORT_AUTHORITY_MISMATCH,
    MANIFEST_TRANSPORT_BINDING_MISMATCH,
    MANIFEST_TRANSPORT_TIME_ORDER_INVALID,
    NATIVE_GRAPH_CONTRADICTION,
    NATIVE_GRAPH_EVIDENCE_UNAVAILABLE,
    PublicClaimGuardError,
    PublicClaimManifestController,
    RUNTIME_OVERRIDE_ATTEMPT,
    VISIBLE_SPAN_FORBIDDEN_DECLARATION,
    current_object_inventory,
    reconstruct_surface,
)
from tests.test_decision_os_intelligence_transplant import (
    OWNER_ATTESTATION,
    graph_index,
    valid_graph,
)


FIXED_NOW = "2026-07-30T00:30:00Z"
PUBLIC_ATTESTATION = (
    "Shin fixes this Manifest's exact surface, span classifications, "
    "evidence contracts, predicates, and bounded manual authority."
)
DESCRIPTOR_ATTESTATION = (
    "Shin attests this descriptor only to the listed native graph boundary; "
    "cryptographic identity and generalized transplant are not established."
)
README_VECTOR_B85 = (
    "c-rk<?Q+{VmVFhL`^Q#wSy_M}2q5!k6`M{p>quTnPJhgFF(5u{Zp)O0l#<R&P1QccKH)yeUVzkx9Xqky>M_-=u8wU{APM50d"
    "(Qy~T>RrmR_W9py*vt07<Uls5IjccrT_oOqvIpFm|suJeEuoDnQ8;&-gf(!-Sc$tT|XJ7-SIdXjgwO-sIFx>H)UEHxY|FC)U"
    "=qJVxC^h>Ke|nh9iQ*$P!CAi*-aYESRx0;u*ox#8G6Z6%0$siR3ht6iXY20>@HnOyLI8?7xkgr@4m9y~Ct4qMfs02O-=UUiL"
    "dDZ@R;A;y$CJe;(hxy~wmM8OJ7ONRkLE!9>hSOc>HErj}5wV-hJtWlT8EFm=_7h@>pklu7q|<)_(vdR5BVb*`WmaCK-ExORU"
    "qPN5OHug-g;H@+#fQF)b5i*)+2FeMZjUFXGT$5T0<n`$oSaHJ^{*!&k$1@r5?3d}F^W;QXwTUq25%KcjvR5Mvr$AOy2s>*Gy"
    "{Hbujd~nrKCMeC{7I|rIpl)#ZM$Q+`a(51!U({q#)o0F1quq53{4Hm*3H+Vq6L*elz)~uAf-E$Abd{N#Ao~PA)bxWX<&_ESv"
    "<$SV@~a~FASb!@H43K1<kO#mase%LV}ccemi1Uapqd8-obtg06+D5GB@|K9QU~*CkeOiMnyJ&A|97K(O>8;+yD8uj<#cg%4Z"
    "jUsDX->vaTSc_u2OW>W&xC$n-|dZhCBdFLNY5PivR<f8YyDTV@m;eR%R>=HHt*Y0GB)igc^ZSj16OPEUCpJmiCLlOo;pC@VG"
    "Ql3XLr%)2pMGfBDBA`&I?m$N^387)NJ=;ajLQ6inZC$Ctz2_=ogtICz`B9(FI@q=WwX4{(Rq2|QExy!T^rnvRFv{^;Vo+aIT"
    "Qo#&^2k)zdz91`Wch9kgOl{wtG46?k?l}E9M*96c7;495+TIKNlCy&DhxJ$^@z^%MTto+fHTY2HyLBKbRoOC`;%ZUz_59s~G"
    "{aL#;xcO!~tcp4R1t=795<o4@%oP4swU=HQcwD%R^A)gAQOzc@m<O^nK{1^Nt`RbLnrow9_*Pmz@e)ZIAQML#FfO7{2_y{_-"
    "~}R51Ovc?=5dH{q(Ukwr5VXM<&=gdRE#T*;@cO!2TlF%xc4sUfDvCOwBrHNc{RA~pLT~ocvoqIr@DKB$K^%pfB<nNEf*8#o&"
    "fQ2?`@JM-*->O>B;4Am;i)_$$wq;h8~YAFQ0#!xfAN=Ob4(2oWKdM;5p9|SFEvMx@p0C0ls0-G@C98ElcMKk94NvqufPp7xz"
    "7;(#pvB1FegJ{sd!~TBBvAVxwusCBoLkp%liLm{OD>YBFXr#En5V(>%mdDWgf4eX(_WZ!gZ1x6oK%{z1PpO1k4^b30E+y(g?"
    "(J-zJ-_cqMh8PjVc-5rruG6ep{SYnhZ5|LQ*$V7w?6~~#uL}&va{K=k&bh?hpj#Ax?JU-LLZXTbm{Gzz$so;xBU7H)30vT3y"
    "MVEo6Gp%0K0isj606{z6k2`Dcc<}+ffCl(!=QeiQ;Hq$+TW0B-hLm@x$yS%VkGPWV>D#1paS1JT(m6Tr_TF}YUwdcJdX4#3r"
    "+?9ovjxOV)d7g)H=X4vwfVkCoL|3xb8-_b>XNB1nJ!EIYN$U6x<Kt_GRd!;Z*<l~vV3T-L%o7o;x#qa!lQUsO}m%lH-lmCM-"
    "PECIXi>k_ov_kTs;FlJBR28{C5NKweo7R<1bQcyJ?x_8eFn7a|B%$0n}3cyripxs&1RAE+Aw<)sJ3A*wLDFXa@U2!+-P5H_H"
    "=W2E7eD1>?0aIiF5vN1G?6)wK+1?4kq3aYSQ9jkdx#^<gpMis8&!5Fat4l!r`12+>Bwp^X_vlyR0t1To^JNCBAeUJHRxRy7;"
    "|iVl?L-B-!Em!>b9XLYUSp;^cq-<E4>R{^q}0cth(GkjZ2H^dj{tEw_(T?DW^4{k?fX!C3NA)l7V!P&ID0pT`W6e}2Q;H+9$"
    "fL{)O!_m@Apwgi001I^l@)vv2xZf8d&grmw<{}L0^auSq?ldm%&TE3r?JfqeO1};~uGkzp8;w~Jd|Z@P0!2RJhDYntD?3t%O"
    "j1W7(O?v-Lky-;G|NP&NrWiaO&}l^6idRDiX(_?gd4&j_8Vak0p@^?(quCIXlkrg5Cwm6K~N%j8-nBx1piw6wRiws%mq&^qX"
    "<-M2$~mY(8e^5kdzUZfFFx&%p*k=VloOdNtDKn04EZgA%?cG!e~6aJQ?3(gZhh0Ao=vw4`7HpZSPzP`dJGFKmm=klqlc5=|S"
    "0x?n#oKpTYk}?J!a8XfEhoO}&0u%6ccJ#$FP*j;t^Bm{!{a?(NW=X0pnw&oTVnVECVB=Y#Lkvu^MFa+stigZ?=Aete*gc2ft"
    "0_RaB;<}tl+eG*z`ro73)k{j~gIh-G>I31i^uGDGz>U{9ZjX13O11mYR)jd1OyWVNiKS}O(WmngoW<U@h+zlEkIC@zuCX<a4"
    "V7@iLo6(?EWx<JDRo(E)$(viFNucoEbNzHD@^yP1he$tc0e!2VEric1m|Ext1Uj!gT7pGo>|#>mYC37gJ0z4T0~uJEPZp&Kr"
    "b;c!>cs<LRHKj}0UBOeE+jDw!UX~vj@&;LF%%hYA!<-XK<r1Fg>g)f4h_==h47H>vH*S!E#Nd~3GlD|&s*z(F3{-m<Rlr5d{"
    "<~=kgV3vwPi<_J?J9!&fQqltzytpHNaEfAxl^OwzSCK7T`8E_k(RKC;iM^pLHBJZFMqudok#{p@HQ49^4g>u?Yt2ML_D5`7$"
    "7Q-P}*^@WXwC>`1Pyj2xmneogPdGI#(+B!+$`v(N*Co@i)oCR{(yAfR99{t2isQ9^>SlTuM(p{rww%B;*{98nbWC$Vw39UJ>"
    "7^<_HtKY!<R93JTScTUG4p*y4F@EPbhY#|*7?h=#WCWnq<1?;+fFo&H0Oj5WJk(rV6${kn~m9&5hRlf(AIzGN$+`u<C3$U3d"
    "$`7V64h3+U%u8?OSvggvdXTG$QrrrKB*Pqf&fJ7?6v;RwSW_z`;(`;$*3uFR(UnmF#4c?}3_+QW*nz9J<!VoWdqUPBiQ7!pW"
    "IM9<F>H^?`eHcnUUP9dycmp<Cowg7G*jQXTe=LJ2c~ZMm@5@KV`}mYOikLy)ML-1j(L@YuJJWQPE&v(^2)zJ_g!Q_wzH6*IW"
    "Pql&I{$=TpkD6Vh$LZyJjq0k&o8~j9RnvvfFL+vd0}L>BffLM>y`f>Oia0r8;mJ0ktsqNGT0;*4_8;Z3T>90?v;CX*c-<khb"
    "jM2Oo357u3Ps$GfAirdfH_L((9`Hgxadq=5rM5XyvAER2vqF$<v|kFCP+Q&TQ8_!#jFE6R0-l))zCUy%kI6GT?82mP4yElIF"
    "ZYM5M(J}+=k7@sK&&)WMlKp*3lkI+Y3j?lXRyvIZIyO0^tqh&@jsp9jS9z;fqMFx#_HyjW>gUE>5Co-1Ju8qwLKOO*mdmx%M"
    "GMgz8O^?2Y&9r9oyjt1PdL+yp9A7^47Cq9y+>wfL7-=1vI0N!lk>y;5JcDq-k!Ca|l+!3?C`2UFMnndBY=#q#56u2t<NS^*_"
    "lDVN#9GembUSAEQE!i#{eEa}AF=79*?s94OQPTO4tyZ_c9T4SY-c1-pMm6Q`$!(Y2)_L`!NLFi&;JIeP2d01%WuC8hK)7BM$"
    "0-a-?lsKO=r_;V~pU&sB17>bpzdfI8a<U3tBm;Ja>8A=Qj-=H<leJK*xh`0wA<xOd~8aDI{YMa%8Brg<ieD5Nuei1;immB>c"
    "ybWHu8l<C^M_ut?XT{|lmEZ~<iQjO$`+@}~Q)HyD0F5*&oXPKAS~;`R!M+hK>J&t$^`m_;~~5yJvBLl#>jFwT&`k|{(%+GcT"
    "Nj8R6wZzSLtH<nw$5!F&jkha;AL_@rtXz)?=Yog)zt{CE-D2DK$7}~8EIA%Lj4DmB4hPZu-A@qtN^opUkF}u9G(D~dchwf_Z"
    "-%Zr>%X}K8P%o+YkeiS7%=N~)AU_%;)GrYL$VC;rA6*XL_1-1#kAwF^XoZpc3lIn&+%mQI56K3~Gq;p9qFDsJH6f@KRtQ53l"
    "bU3LV5t?g7KadntYIn!*<dk=G0Sjd4LQh$7Rv@t#d{(fIOeUE4QxBv;6v#jT{f_t$Odwd4egc<g6>W>uxF4BtbMY9c-cU_Z0"
    "Ldm&)iIcTO$sy@}eGZkjt-^qXtVpULClza_u&D;gYi^(ZH;nUgufvuH|l1pZ<_=;Fxd=YJj82YHDm88%i|<Tc)u^f-oXMPgt"
    "Y{2@N*Z4KGtApd8^biVwn}&BDQx@tz0=LE9}H_;$j<2h%^gaNs);4$(n4w0w~uj&}Eof<J?D;O$cmkyj2;J>YPg_+QnDZ=8B"
    "KnHGg{i{m#1#Bw&{r@+rx1aqj;;mo<lad5Ser9KW^)*PoAT%rj-!q9-tt%T1DN9fM_8)=oA1TeXq69Jf6HiMk_wGbcbs(o!T"
    "V~k^>DCIO`C?Ygu5y8?%Ha02-IiU<OM2B333WeB(c_^oewgeMRL8KhiMvK*kXYf5y8yM4ezupjAu7LC*_>ZnP#7^`EJ?M>=>"
    "kSfyJJTED8T5u|pWdKeZ&0r{M$May;2gqe=`!Ltt&spc7VfCCSCbaXFM@EXbwG4jYfAS@#4WT~u6~%y>gNEE3WhbgUv43bdX"
    "1#hDh_DQa;9EJ*-WdLELT@_rq=#@^H<^FE6cp9)9l<Arz1_HNEry$Qe`p6m?$P(sA92*E!PNQB%>sjluI}o3naCQU3$VyGKt"
    "keT(o(;rYG#ZnRE#uDr)zvON_Qu7(VFk@wCg);Bt79{5pl<8|~2xH&3BG)8@7p!(`;{x=guy5EyM17!ithB``c>z9cXjfb2w"
    "BVDwuli;Y@tw_@|glviLDm!0zN8;n^wbr-0oMXVzWfKma_-2jHejt9b5@+VM9B{$L#9wG=8HX}qDMq-zMm_i@SQcO+EQG_(k"
    "A}it;8|b28jWlISp#$|lh5CELWF6q%CBxoXQ<vSbzNgWB$*B|}*5W)3c*_)rbr9U+L=8J3e7rT`uT}7Y`uC9fIYv99e*CYbe"
    "%vbR@6DUn2!0JEM3G$0m*!i(bx^XH7CxDS%Q_AgI&Q4KO1$qt;fEEJgCLNUQJ>VrAz3e)3{3U%%wS~XJm{{{tGksPCZ9Qc0t"
    "i3KQg?iQh|<g^5PE!(dfw%SY5laTT#LsWZ#_D*(!JVnSsL6K6&wQy9S5%$xtp2M110lw4fAFfkf7dw<4)!3EZx%*uCSQ7-?i"
    "6Bx79>bu@g7EQMh`znWDkedg!V}>Bm&o35j3(>=G_nl^;}Ttl-+FFurPj`wKVcbOpR7S=B?@3Cm2#ETafp&`3(g0%@kB$c0x"
    "NOBD$uBW)$mNJv8!hMF;9!-!ykBg4f(JGE3hc{#E_BPJY&Egv!2HY=s4l06<V*>v5L?nUDuPm)oOPffXb)9z@L3>&97sHQfn"
    "Cc$@>CmMe(G3Am)03Z<MLDxT8I>Dz6cx@w-j&5%ywPBd!wJHD({@JUTT3Iv_1zOT5Xt6-fH(s6G-G-p4_KTyhh_UV|kj1Dw>"
    "}}GibDhVH#{fj`+<Cq4RI}mM-A%KaOjzqUR?8@W99+Zb<7Hd8KV4I}->xOx?^Qzp&RpKCCf(LlEpGhDjX>(G;k?-p_r8orl;"
    "O+>r7*<&OiP49BbnA*Gq(d3#fmGzErKAZ<BU?KLltEi!^C9D@27T1nz5-wHoWP#ks+Sf_hkr2@HXeg##^S^ti$pjJ~1|ae7a"
    "3g<%8jA`VM^e)VUyhazefDy!McKb5D|Fqupi9z|W9-6Spw;W^WFxZK~TlRn~ezt`lRdXP$!f!OW$bn|fnPw<b0N>o2N$_DF*"
    "PDC9BqU{>tVGNLI*mQf@^p&*FJID_t;R>F--L@wMCp)w|8p+v^Am@#chXrO@MhpgCJleOo+y%{qI5pQ|cO1x#($~t!K@tDCq"
    "8xB8-vLBzi^7gi%$=eHX%4PgKj3Dd{Y2)2(ZGpd*%kti>e}6S?|7O`N8-&+ec3%vWQ^!NeeYCyhj?Vw_tM`<?s}s%uc^exk!"
    "aa^}y~tSar)cJm|IN*8{$O8USOXzC14`Ero+8efLPlVtbq1P1WSpQVBM8|@W;C-1LCs>Bfq>#vN%XY|oy!-t8^I!N!q;lA^k"
    "?nY1N7@=ORwN_YMgkemWa`2GMA~(FnZ^kdc4VRDGlE)sykobx25r&BF*ciwdZ*2EWh2@8Fy2~)SJ%U-Zs~5G3;V+?{)uey&d"
    ";S(z|e-xO)7^@2uT@HF6z0M<=(>?p{J4Eba9#F2|dD?mp(!1gEFH(aGRl;`?ilIwef~4Y#VC6JzIzxA1n)mXNdypt<mi5w@*"
    "ql-}OTIepdZpZ5B%A9?=y;5#5tN6}+Hj<{vpu1|mZ)6;t3?2*Nxf|u?c#GpSO4$il{*F#%3-*fIy|9rASe_(U+-DHyYGIw7#"
    "tHG__tp;zIY_`@Vdpv};D?v`5D9BIVbcbX3+D(2s$npJ=<BaS~j?-t6<MbfMj|OgPku$z$>)I3DWGlc8prZ!KL+aaz3==Il+"
    "<`|Bk1!?fg&U8#iDC_MoJNQf$s<ZJgeZ-%Ho~$j%-o*uI6J8C=T_evM!&6h>KUo`iKT;JKM3}NVE@&E9k+S!r_TgCi`p#M<8"
    "1}IQ!WR=j^n3}pnsp7T>21knw*cj>1z--2jRXyJ4B=1jiblUBHZJHa6d|xD$)&-zju-qT(t|lIC_(uzCR95o&I!yn46|V-(`"
    "y49BO~P{O--*+?^tuM3a7Tz}*D|zTl<?d;joO)nUZ2Buo))5F(M1nkk(@NDE2Gu`n@o7a-^%L2Sfg5yl+pSOYMn5t06#b_<S"
    "ND<9q8F<8om2fGGGcMN>=tNIClxh<xD`eL7<wF-(w`!o@Opq6j4h1s^dbR&A0h|sj#Q)E<skb)b+9|!5QH`0mWok=J5EYgV`"
    "q|;G<8YK8QNJ98W;9um^TPAev3=M%#KGpcB)@de&iwB28E!763Oh&^9<Csc<2}Ej1p!QU78gr&ZD1@R68O51K!i0ti<`z_Hi"
    "1dfy(B~cw{q2VspL2}x%OiAcm3gGiYgF$Jlo1xTd7zAMtMDA%9TtZ?K1ull0k@yLu3hA?Kx9vZ9^GMjFa9h-j~|5I(d)H#aG"
    "5yFWRhQb9~k>|8xvW~9n?W;6>`#9Kx_DQtJ78L5QioA*pp7av85Z}`DQVh=K%JO{}#@23s=B<B>3m86)@((wJS2_79kO$EDA"
    "9e*hnQZ97S17t%V17o4KkC#X4dHp4$)}Awe;=h{W(iwQB9kGibkup78ULvM1}q)@mZwh6S@fxvN58tBf`)lP&K9jWKl_1i+m"
    "x$7dbh0*SD`=3;Jnt>fxY|IhyiTWO<X"
)

REDDIT_VECTOR_B85 = (
    "c-rk<>vG#TmVOnM|7=xPlmdtgf$X1EY&y}7ZFwX)ot~W(3&h3djx1?NDczZ_uF5;?-<g-olk5Sgn;k2$9A!**E0szl5g;z-J"
    "LmfVl83(@s45$~gBJ%eig^nqErJIKy$FB*a`5ax&8Ao5vY39zuE)kgxzqO9Mf)V{{&<%5vi4w*_6O+^6x3I$oZ2!gEu8Jw13"
    "ey1?P!`^sp<-9IV%vsF?GZ-k#Ivvj%8vUqar6*Sx%{CP9|6>L6l&zVpusIOU#urm_Y;M{C};UW`%*%y}_i_XRYI23nAR<U7W"
    "QJU$=XM)PF|@zdgI%JdG6>+Hq<%MUv;5Fe5Na6f=xCMH!PhB8tWo4icUxBBng&TpJPR#2G)n^2200zAV+`s?g92I6KS=ocpX"
    "h$Y2uMFHbuC*I_D*)kRf|N7?x2ku9M}|Ed^$_IswLQ(H~d6n>ePiCpoEt)l5wQAPF_bv+r{=v0jg2j%{wimHhkRnH<lR8>{D"
    "LWipGgMIJ2qis~$zt4)&UPIsD=W8{cdCT4U+5V!3v#PE+DXsD6vG7?<CPVm~7eimiPhhFEub@T-zWUBgZIpk2fAsjhE!Cxs+"
    "_;R4t%}Q0^j-}M6M7VlN5c>Q8I?1bp=%p05wz&XYJhqgjiAbV8&xm@tx71O$EAs;<0!XL*H2SxUjHA~gr2x^{0}>VQ<US`<r"
    "VyI;Y>v}Ek>77f9gBMmU9+CnW=paQ*X%zU=or$sS?T@G0ZB-vEYsY@SMt%I5vpNI00OW91v<HMjYED;ao9?C0Fi?z)Xq%&*O"
    "1nq6{Wm4ab)UFaGD(C+u4lV50yu!7vVvyS-EBG!)EE+k=Z<XYf;Y-0PlZuX^qC*ID=M<R@t1RSIKjpLG6`9%X}G`>cO{(moq"
    "xx1HzRzsb?+pF9%Pw1y+VSeFH~Tt;~@GF3ovfY%Vv1>h^~WLy<+{6oOu9JmX})xfQSM=br(ms@(_%0a+4tQxj{9+yKCEe06;"
    "#DA>a8r*z+9+t(t{{j?7Y8XK;?Zl2kQ?-{~S{N=g<9!7zG^!>;HJV1Mw9#lhjr=6!Fq$iCo`+dljCg@01CZg=0LCSawM5E7T"
    "ufp~HNgNdX#|fEraESdF_x2DFu_=CW1R>s5WjiSJJ5929(3NMEimG%l(hmtS}(g7XGiVcPr+51;Hkb%@VH`>c_2Vs$;#Q#yC"
    "*<=&^b-B^lkfakR4w1dMQA-m;U*p(+hZ9dinIj#8;@tnRQ?OcM26=!Z=S-Uu<r{Y~6x)0({M&Sw5bPj4Hh++|!w!9TYxl`?w"
    "!4l~q<vH_R^Pgvunr%vqyy&8=a%PzXEAV<oM%oH3LmX7j}6NLY(p4&;cH*4B_X|KjX+PR~!$Q<y9;fA_4_PuqjVbbC+8f+s9"
    "pJ-g`%cTUX88M7;^e2d6v6<ek-Ru}=nQ^Jj)mJ&iV=efm18Vg@S<-kKGTSaA0slK6r&unhDfKOk3Ho9X}aG=sx_F82?hE?6s"
    "Mc`?TtLJrqXjMKyuvYNn*2+7czemqu0^aT1#$Fp-j{NtAS^9cT$~)9#%TwM(T<OtKXV5yofSEdM9iFs1r!C;u&N0m1+<eRGU"
    "$o<71~F5&03yY8Yf+^(-xrDV>+R1g&x1u>G7BZMMagf5`h%bg)NY5v;?ny@YegiBK?fZg6ik>DuW9V%IH2~t*F8-8{p|drci"
    "!#$U{@E}JV8gj_OYK3G@qlodp9+1maD4p{&`awWyhVj-a9&jlQjFh<-H7Vo(vyBjDxNpybyd{6wgN)qSb@&GO^`#0ft<Q>E5"
    "k^Kt1XnUMxdW_VT3r(#y;x2`pmn7upO6Yt0eXnj`GCa9N&koL9Dd@6T+n)cax#&>PK$!?hA%wiUML+JD*0-cO;AUQ8dpzOi<"
    "Ic<u-E&MOGz0|y8RsQJSWohY9bLlAmV7z~(bQjWE)YB>t<8+o&gM>cAAT3{Q{giaO18R$ZA^)b{d?W_WAXluZYhd=yqu--~m"
    "U8$IH&mOT=Si~{JWu&Ag(jf&xP)VenmeNXQ5!N!sG=Y!=Ul_Iscn0W&QU@}}pB9i0oy>fgDFOSn^W9!dEU5%s+_T==dT6awF"
    "TLo0USI=x_Ad@YjJQ?0j=VKI`WGD_*UpJw#oQ<cvtBz%7N|U1`s~8Gf1iQtxgspnmX7|J=|7Vk>vlivo}PElyr@jycA(X>!*"
    "m^3V9aY!OFpJAf=UoaXX!jBFQ_DVhW~8}>&CgmA^18gor0$C;amr+(o545i=6{|^8`5A<RHDZ!G>vts8TW}ImLvdIJZDXf+a"
    "bu5x9vhP`3phXBw~!Yu@2-{Ijj2Km~;Mi{~?i)Xm@^ZbAI7qrZ+e05b7BXcVQe0EuDw0*c0Q#wk*Y3Y8G#kmG`CrcnZ*%@u)"
    "OCj{gTaXCuRV(RV_ar%Sa#o>az*C)I_Z~>6ZUj77txi$Ab*uj!{rom`nz=i35eBFVv=k3EZJ2{5G2hA|iXQaLebY2$^f=fP#"
    "*W-Kh`j6e-pN>zuKi1xz^*a4Ofp0)0cstnhdb4>wCS+&C9)EXYzoX4o`lfT_BX48)z3t65D@$(z;B{c>YoP5FmBZ@!Zw{hr6"
    "&3RhtyyK=Y#3F_*~^*o+fsfD$P`sT7FgQM%7r2*Mmj9KK|%mrEF1@H03JQuhegl?OK|{>VW-ve4UyO(iAkKq9DzijMq`5rPm"
    "mExBkCj<uz-U#C09C;5Tpr600!$72t(XB6qYMrk_LND|BTZ;Pd1g*V{|Jn&|9#MHo%B*C2itBM6z7O&gD`jlvo4|PBrLDBZ!"
    "uY5+HcZqyv@dh|ZnLIi?J8@gPEvw<Gir<-W}5;osjmqmz3x`gt!67YEX8>BjS@J@3h$*PG4j5XpDO>*Nu5oivZv2VjE{e2i)"
    "uzgFJV6B{l_foT<hV7^L!76D*XG#qO+^k5HV!P511a_&uBMV~(Yb8Rd6)5m{72>==}{4~0P<GJ<rx8Yir9ai?|E06-4xLhYH"
    "CN@c^0y@_$p@t?gurx->!~`*fvBOjmNu(e#6P6i5osAVmSSHTxxqMqL4+QySR_KJwhA+{{c8nh4+Y?@+_q!Lp!}JC&w-3y83"
    "qJ22!E|QxW`W-OzSYIm{ymj9n96A^cShy(D^xzm$8I>BelHGR>*aRzy}b4crddq=wbfTJ`_;8yhF1V+Fzync9__Yzu^~{3Tq"
    "e18SP57f!#Y`^gj2-`K~hj=B}D=$i40;mhFB>SP&6D!IK)+<MgA4m?VbbadKUFDFn!&A)9LoUu(ke2*?{l#(p4mTllD5t^S<"
    "ni+XGuZ8E&TpH=Nt)cHABU-V^5byJhG0!J6Hh-WQ@5K8AZ?)|D^b^Lw-T9TsOh<9GH5OLf+~rFtt$@$wc=Z;<7}d{T}l;|eU"
    "dr2Q3IYhXDwtO6}<T5AjG5^fVh5*r)N6*3l+*ci$LH^BKcj*$^@94B01%5wjkOem;?JWn)__pIOGWqlyi=2HKyz!85&{2MTf"
    "aIR>AC9r<Zos}5pNMe;}FHLFAskK&H3I8JrzX|JvlL9dVqLxvfKZy3(cC;Vj;MZvX_s;ozC!8PeIltkYPj<IG&mV#Fc_TSLU"
    "Kv-7)}FVRg85A`-9+fQ!&W$0rWj+S<VInVFl=&{$Iht4GL9W3ln{dj(!yWQ<T6&;NRkMr&7RO3Oz43mp9-N9(P%>FTM{}+_J"
    "p47gwV;J&>K$Za(9HDJOZI7jU;rkgf19dYdi59_hCY-V6~giQbmiAZz6gQ3=M%HW|Uc`xHK{+!ZHYp$_Nn);#7D7mtyUZBZe"
    "4>DYqiA1eWh=zhB>Iq9@|%5WQ?R(I;CHz1$N$5<4M!x+nT(6Fui*XGAX^f#^jeiJs1rIDk2>qws_q%&aawV!|Eq&m#X!|Fdv"
    "E+_R{D7&hExH;2u5<8D3TOw!oJl3;F`L?ThrBIk^CHivjYl0*{0V`YiWwc`q62}&pjl>lm>PI0j3{HAigd^()Z@3;l8Nt`dX"
    "<NOc@|LB}Acf$E>&-u;f{6y~V4m|k?oG%;6`3yj)hBJ?(`Z2ihxEde<*uSz9Rl*T4@^vu;BTrTJw+J8z7Sn20so~l^dNY0HZ"
    ">SGj{y@-vo4`ZL8_9Z&Fn>mVXlqQWvZ%(RO?ts#VF|-R<_^M#kq~>ZHi#*Lk)}D}u@Q;SY6OCT#{wW|WR8*~);ThgC40TlV7"
    "<Vf)Qx=tHT}juxt(SRar6&<(>_L9-?YE-i2d#RPft8xgm(6beE`qD>;8R=8h8KxwJk5fEIzLlV8U2`JD;ys&9?+RSk-7eD*S"
    "_YK5v=F*)nI}dQL}=))A0Z)b|hY0Sas}@z?|QvigHwW!8b;RvEoold^d4Wl6|77*+5a0AP8pI`!7LoYoljX?m1tg~XKJ?`Bo"
    ">zOX-UQXUD$M8-}aYZAp`E0j?-ah79lbS@~3Z5}fPM<r9rN-J}vwIS4E3t|QBl}9t5CI~eCWJCvqE7ok)fzfuVqYl7-_<TP2"
    "{(1V=CN$))d<&tY6ZHAXJ^{d!ksZ6cP=UXevhU8sx!<fm@b}Um^R%&b!fO!IM?U1IcZrZK^CAD&H)mwt@YEt`3ZEGoKs6gqe"
    "cm9SU<hy?l*J;jJ*%@u{{ogO!c7swO;UpqOlh7I<FoupMxcGmD5JTQghFUeIN{i6jje_?8-_6vhjJkuMlQ|`ZdAGe0CYVW*("
    "H3>tXBd)sJ-fjSTvlfEIh`!I&#=PJL(*HllyU4J*%@V2Z^>S)jssb-jLOKS*(WJby4}fsg-MlS@(01((GoE-RxxtT0eW`hqR"
    "Vac3rmA$y#rwn@vg9hUq&Go5`L2VHdQD55h1J)jS_{y(}CA61i1*V<&E$p#5@FeO4>IyNkd3?ZNVELjvb7>#lY4eNBATa^{I"
    "7U4ob`8=Q3s<86i4*RK&ZI_=UOuS$53^16Q}#hd;xf00Aj=E>Uqe%hNaO!msF$;u03v@_)uKZ^2-_sZ+wIB-wYn~fqke@Mv`"
    "c5>7LAoI7pY|>Z~LAbRRC6-Ff84<`jhq1qC1UibL#6Z_HvzUlnNopLdr9-NJVuTa!YZ_~@IlM3w#D{Diua>WMdDLy04YI5T$"
    "z8InKC)4d)rY@9i`7TBkX%0Q&qMHig_eJTf{)alS7)d7%SH~<&iUY;GOK+7?wEDX&MyY*ZxpzfLc^O>;pQrF78=~DbN*VyNg"
    "6=0-PrD-UpLqNM)`Wu{SjEyn{&|X1P9q_ZdcVGKKd^T=+BDJUo7QwDEGQ2Teh|7#S{%t?)Tg=t#$BI5$*7&$)bJBRH?Ok*^7"
    "2e9w^$+x)}sx_>jI$4=+Njcm*0~uiu}JewS=#`kg$AekXhVe$c7YsE)=_ia&k)zi_+RBG1cGWcsbtTd&%y;p|cK%3tXPuTaI"
    "Pie7h5jy6es0HzaM$4QL+{p1R36=Q)_f{hYj7lDWn2FwDz=1w`uCFPbPNg=))?tZ6I|G>}L!Gpy9J>RYOy_Em=SJRIvhnuyV"
    "dtXf$WY*KUjE=(t!A-u5PPP?>o)-6)(eIyhchf5&(^s{h>@TH15kW}M?k=U%M-hZ{F9;6?;kD6YdrR@HUeH|HNjWwU-sbOf9"
    "#>V%4|5pas8eV4Uw>uur;q<!fAi+rE1aKy`uML6p<WS)SK4AhoU;gii(`i4M8r5zf-)LgtGSd^id=!1Bvf*$B||J>GFBvi3Y"
    "Xr$=N|9<U$pyRHP~1M6dtpGY-)Yy&k7N&vc@h=wrB??W9(nS4J};^j$5JuT3~g~+0=<zwbe2GxBmwhykZ~"
)

DESCRIPTOR_VECTOR_B85 = (
    "c-oCr+j65u5d9U3XW?QPhKuurZEP#0ix;6yoK$M6nQ06u1PY9_QMU5$X|Uy8C*G~RsKiX)&gpaJvkeDRb$xA4a@T3JFYRTr+"
    "9nIR{%MtFGRgCFlczWK%vKfj27B3KX<vS}Ro5D9jjUj(D67QC<;?R-UWzCTw9g9`hgb?fDmViSd>=&_hYTR%5D5<igEH`976"
    "51_s6ki!j>^bdQ@M|fI~(ELW{&GJC)=)^>-!|j)A8H2|DKKQ2h&5{n!&#O)xKS4OB$L2<ub{)**t%gx7m6r@3Q3KUanV*N9u"
    "5w5~gG^|0TVVd6uj;4~t}#%hfuUgfh8W%s2Oh^*1WtpZ2DE>S15iibf)&L=g@4@7S5GQPo4;wX*xvVoxEPs&4;tF2NWa3>Z3"
    "jiLsuK2Fp}n=%*emjf3iI>fBpJ-Ri;W+U7)8Xf^d<P+L9jyP>B0lLf7|TB>(MYh&OEEkU=c>nW?Gd_0a*E1cqXU=HJsts^wG"
    "o`(2=qM>m<b$z3)GeB!p!}wQCF*EB853gY}3;!f3w9r^ICGN4ETFs_jPe^d7&0jPwZKxgg4YbCB9<8=B)<{A@Xe!hf6H8~rX"
    "C-NpOyFxbV6pG1*aZ}E5qhz&I3t0@Ito0O`N|U@geZ6siAV?!JrzbOa)Y-;-%-;l$>$$ahn9Gk3TG0CbG6>CZj$VA44?wYza"
    "ewZi!z4L7bVvMAr4p+l!9bj0?p`Y*N?rBR2~(icZ?aKz%UE~5G9KPD8DQ7luzwR-FO^(lH=-DjzXy0C)ppG(Visne7;O&`g3"
    "xf%j<2Hr6l1j{ji;9lOE5Dm*%t|6P|I(_0^9lC0r5CMLLGPY*2o^!FL7z)k0;_9a;_j=!E}irkP#u_6_a`(4;9jAee8k%L4A"
    "lVaP;@8VVJl7DWUuD>3jOM#Mk}w{Qg(Ar@|g=$3_!JO)ak=3en#cIV57MY<%iX#MMzvq_WuO!w#nIXU6g>hi4<-X-RX8D)hq"
    "c67A@4+Ss=%q<l6d7vX7ea^WGf&v+jHPXkF{Kuj0iPG17sRo8&Y&7XpzU*z%=NNxz-$6wegQ{=`@`(NLJm~r1ak}B+`GIhT@"
    "qrM|<YVWHJ1&my1rhKMaKrBr"
)




def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def create_repository(parent: Path) -> Path:
    repository = parent / "repo"
    repository.mkdir()
    git(repository, "init", "-q")
    git(repository, "config", "user.name", "Public Claim Test")
    git(repository, "config", "user.email", "public-claim@example.invalid")
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(repository, "add", "seed.txt")
    git(repository, "commit", "-qm", "seed")
    return repository


def _replace_refs(
    value: object,
    refs: dict[str, dict[str, str]],
) -> object:
    if isinstance(value, dict):
        if set(value) == {"content_hash", "object_id"}:
            object_id = value.get("object_id")
            if isinstance(object_id, str) and object_id in refs:
                return dict(refs[object_id])
        return {key: _replace_refs(item, refs) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_refs(item, refs) for item in value]
    return value


def graph_through_e3(repository: Path) -> list[dict[str, object]]:
    source = valid_graph()[:9]
    head = git(repository, "rev-parse", "HEAD")
    refs: dict[str, dict[str, str]] = {}
    rebound: list[dict[str, object]] = []
    implementation_seat_source = source[7]

    for original in [*source[:7], source[8]]:
        record = _replace_refs(deepcopy(original), refs)
        assert isinstance(record, dict)
        if record["object_type"] == RUN_CHARTER:
            record.update(
                {
                    "completion_line": "Public claim guard test graph.",
                    "repository_head": head,
                    "source_freeze_id": "GI-PUBLIC-CLAIM-001",
                    "source_freeze_sha256": "a" * 64,
                }
            )
        record = object_with_content_hash(record)
        refs[str(record["object_id"])] = exact_ref(record)
        rebound.append(record)

    e3 = rebound[-1]
    seat = _replace_refs(deepcopy(implementation_seat_source), refs)
    assert isinstance(seat, dict)
    seat["allowed_inputs"] = [
        (
            "E3_ACCEPTED_DISCOVERY:"
            f"{e3['object_id']}@{e3['content_hash']}"
        )
    ]
    seat = object_with_content_hash(seat)
    rebound.insert(7, seat)
    return rebound


def transport_for(
    record: dict[str, object],
    *,
    context_ref: dict[str, str] | None,
) -> dict[str, object]:
    payload = canonical_json(record)
    return build_intelligence_transplant_transport(
        payload=payload,
        source_path_or_label=f"{record['object_id']}.json",
        mode="BYTE_EXACT_FILE_IMPORT",
        declared_sha256=hashlib.sha256(payload).hexdigest(),
        context_evidence_ref=context_ref,
        as_of=str(record["as_of"]),
    )


def attach_graph(
    controller: IntelligenceTransplantController,
    graph: list[dict[str, object]],
) -> None:
    charter = graph[0]
    controller.freeze_charter(
        charter,
        charter_source={
            "completion_line": charter["completion_line"],
            "freeze_id": charter["source_freeze_id"],
            "frozen_intake_sha256": charter["source_freeze_sha256"],
            "repository_head": charter["repository_head"],
        },
        repository_head=str(charter["repository_head"]),
    )
    for record in graph[1:]:
        object_type = record["object_type"]
        if object_type == SEAT_ASSIGNMENT_RECEIPT:
            context = None
        elif object_type == E1_DISCOVERY:
            context = dict(record["discovery_assignment_ref"])
        elif object_type in {
            AUDIT_INPUT_MANIFEST,
            E2_AUDIT,
            AUDIT_COMPLETION_RECEIPT,
        }:
            context = dict(record["audit_assignment_ref"])
        elif object_type == E3_ACCEPTED_DISCOVERY:
            context = dict(record["audit_completion_receipt_ref"])
        else:
            raise AssertionError(object_type)
        transport = transport_for(record, context_ref=context)
        if object_type == AUDIT_INPUT_MANIFEST:
            controller.freeze_manifest(record, transport=transport)
        else:
            controller.attach_object(record, transport=transport)


def descriptor_for(
    *,
    charter_ref: dict[str, str],
    e3_ref: dict[str, str],
    implementation_seat_ref: dict[str, str],
    repository_head: str,
    run_id: str,
) -> dict[str, object]:
    descriptor: dict[str, object] = {
        "authority_mode": "MANUAL_OWNER_ATTESTED",
        "charter_ref": charter_ref,
        "constraints": [
            "FORMAL_RUN_MATURITY_FROM_GRAPH_ONLY",
            GENERALIZED_BOUNDARY,
        ],
        "cryptographic_identity": "NOT_ESTABLISHED",
        "decision_owner": "Shin",
        "decision_owner_attestation": DESCRIPTOR_ATTESTATION,
        "descriptor_hash": "",
        "descriptor_id": "PUBLIC-CLAIM-GRAPH-DESCRIPTOR-001",
        "e3_ref": e3_ref,
        "event_chain_binding_rule": "RUNTIME_EXACT_CURRENT_REQUIRED",
        "evidence_type": "STAGE5_OBJECT_BUNDLE",
        "external_independence": "NOT_ESTABLISHED",
        "generalized_boundary": GENERALIZED_BOUNDARY,
        "implementation_seat_ref": implementation_seat_ref,
        "real_world_identity_authentication": "NOT_ESTABLISHED",
        "repository_head": repository_head,
        "required_evidence_class": "NATIVE_STAGE5_GRAPH",
        "run_id": run_id,
        "schema_version": "decision-os.native-stage5-graph-descriptor.v0.1",
    }
    descriptor["descriptor_hash"] = hashlib.sha256(
        canonical_json(descriptor)
    ).hexdigest()
    return descriptor


def claim_span(
    *,
    surface_id: str,
    text: str,
    claim_id: str = "public-claim-001",
    category: str = "PROCESS_PURPOSE",
    evidence_type: str = "DOCUMENTATION_BLOB",
    verification_mode: str = "DOCUMENTARY_BLOB_MATCH",
    observed_behavior: str | None = None,
    boundary_id: str = "public-claim-boundary-001",
    predicate: dict[str, object] | None = None,
    maturity: str = "NONE",
) -> dict[str, object]:
    payload = text.encode("utf-8")
    return {
        "claim_category": category,
        "claim_id": claim_id,
        "classification_basis": "OWNER_ATTESTED_FIXED_TEST_CLASSIFICATION",
        "decision_owner": "Shin",
        "decision_owner_attestation": PUBLIC_ATTESTATION,
        "end_byte": len(payload),
        "evidence_contract": {
            "claim_id": claim_id,
            "permitted_evidence_types": [evidence_type],
            "required_boundary_id": boundary_id,
            "required_observed_behavior": observed_behavior,
            "required_verification_mode": verification_mode,
        },
        "evidence_refs": [],
        "exact_text": text,
        "exact_text_sha256": hashlib.sha256(payload).hexdigest(),
        "excluded_interpretations": [
            "GENERALIZED_TRANSPLANT_SUCCESS_NOT_ATTESTED"
        ],
        "native_graph_predicate": predicate,
        "qualifier_requirement": None,
        "required_evidence_class": (
            "NATIVE_STAGE5_GRAPH"
            if predicate is not None
            else (
                "BEHAVIORAL_VERIFICATION"
                if category == "OPERATIONAL_CAPABILITY"
                else "DOCUMENTARY_COMPONENT_EXISTENCE"
            )
        ),
        "required_formal_run_maturity": maturity,
        "span_type": "CLAIM",
        "start_byte": 0,
        "surface_id": surface_id,
        "surface_sha256": hashlib.sha256(payload).hexdigest(),
    }


def manifest_for(
    graph: list[dict[str, object]],
    *,
    repository_head: str,
    surface_id: str = "public-surface-001",
    text: str = "A bounded public claim.",
    span: dict[str, object] | None = None,
    object_id: str = "public-claim-manifest-001",
    supersedes: dict[str, str] | None = None,
) -> dict[str, object]:
    charter = graph[0]
    seat = graph[7]
    e3 = graph[8]
    selected_span = span or claim_span(surface_id=surface_id, text=text)
    payload = text.encode("utf-8")
    descriptor = descriptor_for(
        charter_ref=exact_ref(charter),
        e3_ref=exact_ref(e3),
        implementation_seat_ref=exact_ref(seat),
        repository_head=repository_head,
        run_id=str(charter["run_id"]),
    )
    if selected_span.get("native_graph_predicate") is not None:
        selected_span = deepcopy(selected_span)
        selected_span["evidence_refs"] = [
            (
                f"{descriptor['descriptor_id']}@"
                f"{descriptor['descriptor_hash']}"
            )
        ]
    value: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "manifest_schema_version": (
            "decision-os.public-claim-manifest.v0.1"
        ),
        "object_type": PUBLIC_CLAIM_MANIFEST,
        "object_id": object_id,
        "manifest_id": object_id,
        "run_id": charter["run_id"],
        "as_of": "2026-07-30T00:20:00Z",
        "supersedes": supersedes,
        "content_hash": "",
        "manifest_hash": "",
        "charter_ref": exact_ref(charter),
        "e3_ref": exact_ref(e3),
        "implementation_assignment_ref": exact_ref(seat),
        "repository_head": repository_head,
        "surface_id": surface_id,
        "surface_sha256": hashlib.sha256(payload).hexdigest(),
        "surface_utf8_bytes": len(payload),
        "surface_encoding": "UTF-8",
        "spans": [selected_span],
        "evidence_catalog": [descriptor],
        "generalized_boundary": GENERALIZED_BOUNDARY,
        "authority_mode": "MANUAL_OWNER_ATTESTED",
        "decision_owner": "Shin",
        "decision_owner_attestation": PUBLIC_ATTESTATION,
        "cryptographic_identity": "NOT_ESTABLISHED",
    }
    return object_with_content_hash(value)


def evidence_for(
    span: dict[str, object],
    *,
    repository_head: str,
    event_chain_head: str,
    evidence_type: str | None = None,
    verification_mode: str | None = None,
) -> dict[str, object]:
    contract = span["evidence_contract"]
    assert isinstance(contract, dict)
    payload = str(span["exact_text"]).encode("utf-8")
    return {
        "boundary_id": contract["required_boundary_id"],
        "claim_id": span["claim_id"],
        "evidence_id": "public-evidence-001",
        "evidence_type": evidence_type or contract["permitted_evidence_types"][0],
        "event_chain_head": event_chain_head,
        "observed_behavior": contract["required_observed_behavior"],
        "payload_base64": base64.b64encode(payload).decode("ascii"),
        "payload_sha256": hashlib.sha256(payload).hexdigest(),
        "repository_head": repository_head,
        "verification_mode": (
            verification_mode or contract["required_verification_mode"]
        ),
    }


def evaluation_packet(
    manifest: dict[str, object],
    *,
    event_chain_head: str,
    evidence: list[dict[str, object]],
) -> dict[str, object]:
    surface = reconstruct_surface(manifest)
    return {
        "content_hash": manifest["content_hash"],
        "evaluation_id": "public-evaluation-001",
        "event_chain_head": event_chain_head,
        "evidence": evidence,
        "manifest_hash": manifest["manifest_hash"],
        "manifest_id": manifest["manifest_id"],
        "owner_execution_authorization": (
            "Shin authorizes this exact bounded public-claim evaluation."
        ),
        "repository_head": manifest["repository_head"],
        "schema_version": EVALUATION_SCHEMA_VERSION,
        "surface_base64": base64.b64encode(surface).decode("ascii"),
    }


class PublicClaimCanonicalVectorTest(unittest.TestCase):
    def test_exact_readme_reddit_and_descriptor_vectors_reproduce(self) -> None:
        vectors = (
            (
                README_VECTOR_B85,
                44872,
                "9bd9eb81e670a341c9796836370d765f351d634ce5a6381b15b19743a572d57a",
                "818f146b3488a0003de880df132384550aa1058e5589c3e6919d47b9836e9531",
                2506,
                37,
            ),
            (
                REDDIT_VECTOR_B85,
                33614,
                "42a68cf64ec4096bc35d8157a5d53fa4559b03a42496b36b78246b66cd82b3fd",
                "4896df8cab03ce528dce6276f0754de137cd9072061c93a7010ef2febb4398fe",
                1308,
                27,
            ),
        )
        for encoded, byte_count, self_hash, payload_hash, surface_bytes, spans in vectors:
            raw = zlib.decompress(base64.b85decode(encoded))
            self.assertEqual(byte_count, len(raw))
            self.assertFalse(raw.endswith(b"\n"))
            record = json.loads(raw)
            self.assertEqual(raw, canonical_json(record))
            self.assertEqual(self_hash, record["content_hash"])
            self.assertEqual(self_hash, record["manifest_hash"])
            self.assertEqual(self_hash, object_with_content_hash(record)["content_hash"])
            self.assertEqual(payload_hash, hashlib.sha256(raw).hexdigest())
            self.assertEqual(surface_bytes, len(reconstruct_surface(record)))
            self.assertEqual(spans, len(record["spans"]))
            self.assertTrue(validate_object(record).valid)

        descriptor_raw = zlib.decompress(
            base64.b85decode(DESCRIPTOR_VECTOR_B85)
        )
        self.assertEqual(1541, len(descriptor_raw))
        self.assertFalse(descriptor_raw.endswith(b"\n"))
        descriptor = json.loads(descriptor_raw)
        self.assertEqual(descriptor_raw, canonical_json(descriptor))
        self.assertEqual(
            "d54864d061942c90ae59b7294c311249d862014c25a555b3b858552e2c78c806",
            descriptor["descriptor_hash"],
        )
        self.assertEqual(
            "bc6835bc9e2ecea2293bd42488f763ee8a17b21cb0bb58f80d39371199e0fa78",
            hashlib.sha256(descriptor_raw).hexdigest(),
        )
        descriptor["descriptor_hash"] = ""
        self.assertEqual(
            "d54864d061942c90ae59b7294c311249d862014c25a555b3b858552e2c78c806",
            hashlib.sha256(canonical_json(descriptor)).hexdigest(),
        )

    def test_public_schema_is_strict_and_native_schema_owns_sidecar(self) -> None:
        root = Path(__file__).resolve().parents[1]
        public_schema = json.loads(
            (root / "schema" / "v13_public_claim_guard.schema.json").read_text(
                encoding="utf-8"
            )
        )
        native_schema = json.loads(
            (root / "schema" / "v13_intelligence_transplant.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            "https://json-schema.org/draft/2020-12/schema",
            public_schema["$schema"],
        )
        self.assertFalse(
            public_schema["$defs"]["evaluationPacket"]["additionalProperties"]
        )
        self.assertIn(
            "PUBLIC_CLAIM_MANIFEST",
            native_schema["$defs"]["baseRecord"]["properties"]["object_type"][
                "enum"
            ],
        )
        self.assertFalse(
            native_schema["$defs"]["publicClaimManifest"][
                "unevaluatedProperties"
            ]
        )


class PublicClaimGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.repository = create_repository(cls.root)
        cls.graph = graph_through_e3(cls.repository)
        cls.native = IntelligenceTransplantController(
            cls.repository,
            clock=lambda: FIXED_NOW,
        )
        attach_graph(cls.native, cls.graph)
        cls.head = git(cls.repository, "rev-parse", "HEAD")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def freeze(
        self,
        manifest: dict[str, object],
    ) -> tuple[PublicClaimManifestController, dict[str, object]]:
        public = PublicClaimManifestController(self.repository)
        readback = public.freeze_manifest(
            manifest,
            transport=transport_for(
                manifest,
                context_ref=dict(
                    manifest["implementation_assignment_ref"]
                ),
            ),
            repository_head=self.head,
        )
        return public, readback

    def test_asset_and_native_manifest_identity_are_exact(self) -> None:
        self.assertEqual(
            (
                "decision-os.public-claim-evidence-guard",
                "guard",
                "v0.1",
            ),
            (ASSET_IDENTITY, ASSET_TYPE, ASSET_VERSION),
        )
        manifest = manifest_for(self.graph, repository_head=self.head)
        self.assertTrue(validate_object(manifest).valid)
        self.assertTrue(validate_graph([*self.graph, manifest]).valid)
        self.assertEqual(manifest["object_id"], manifest["manifest_id"])
        self.assertEqual(manifest["content_hash"], manifest["manifest_hash"])
        self.assertEqual(
            manifest["surface_sha256"],
            hashlib.sha256(reconstruct_surface(manifest)).hexdigest(),
        )

    def test_dual_hash_identity_and_complete_coverage_tampering_fail(self) -> None:
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-tamper",
            surface_id="public-surface-tamper",
        )
        identity = deepcopy(manifest)
        identity["object_id"] = "different-native-object-id"
        identity = object_with_content_hash(identity)
        self.assertFalse(validate_object(identity).valid)

        dual_hash = deepcopy(manifest)
        dual_hash["manifest_hash"] = "f" * 64
        self.assertFalse(validate_object(dual_hash).valid)

        coverage = deepcopy(manifest)
        coverage["spans"][0]["end_byte"] -= 1
        coverage = object_with_content_hash(coverage)
        self.assertFalse(validate_object(coverage).valid)

    def test_freeze_delegates_one_event_and_projection_is_neutral(self) -> None:
        before = reduce_evidence_graph(self.graph).as_dict()
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-freeze",
            surface_id="public-surface-freeze",
        )
        _, readback = self.freeze(manifest)
        events = self.native.store.read_events()
        matching = [
            event
            for event in events
            if event["payload"]["object_id"] == manifest["object_id"]
        ]
        self.assertEqual(1, len(matching))
        self.assertEqual("MANIFEST_FROZEN", matching[0]["kind"])
        self.assertEqual(canonical_json(manifest), self.native.store.read_transport(
            matching[0]["payload"]["transport_sha256"]
        ))
        for field in (
            "execution_status",
            "delta_state",
            "current_gate",
            "missing_evidence",
        ):
            self.assertEqual(before[field], readback["projection"][field])
        self.assertEqual(
            (
                "ACTIVE",
                "CANDIDATE",
                "GO",
                ["E4_IMPLEMENTATION_BINDING"],
            ),
            (
                readback["projection"]["execution_status"],
                readback["projection"]["delta_state"],
                readback["projection"]["current_gate"],
                readback["projection"]["missing_evidence"],
            ),
        )

    def test_exact_implementation_seat_and_transport_time_are_required(self) -> None:
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-authority",
            surface_id="public-surface-authority",
        )
        transport = transport_for(
            manifest,
            context_ref=exact_ref(self.graph[8]),
        )
        with self.assertRaises(PublicClaimGuardError) as caught:
            PublicClaimManifestController(self.repository).freeze_manifest(
                manifest,
                transport=transport,
                repository_head=self.head,
            )
        self.assertEqual(
            MANIFEST_TRANSPORT_AUTHORITY_MISMATCH,
            caught.exception.issue_code,
        )
        self.assertFalse(
            any(
                record.get("object_id") == manifest["object_id"]
                for record in self.native.store.read_records()
            )
        )

        time_manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-time",
            surface_id="public-surface-time",
        )
        wrong_time = build_intelligence_transplant_transport(
            payload=canonical_json(time_manifest),
            source_path_or_label="public-claim-manifest-time.json",
            mode="BYTE_EXACT_FILE_IMPORT",
            declared_sha256=hashlib.sha256(
                canonical_json(time_manifest)
            ).hexdigest(),
            context_evidence_ref=dict(
                time_manifest["implementation_assignment_ref"]
            ),
            as_of="2026-07-30T00:21:00Z",
        )
        with self.assertRaises(PublicClaimGuardError) as time_error:
            PublicClaimManifestController(self.repository).freeze_manifest(
                time_manifest,
                transport=wrong_time,
                repository_head=self.head,
            )
        self.assertEqual(
            MANIFEST_TRANSPORT_TIME_ORDER_INVALID,
            time_error.exception.issue_code,
        )

    def test_payload_and_receipt_mismatch_block_before_immutable_write(
        self,
    ) -> None:
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-payload",
            surface_id="public-surface-payload",
        )
        altered = deepcopy(manifest)
        altered["decision_owner_attestation"] += " Altered."
        altered = object_with_content_hash(altered)
        mismatched_transport = transport_for(
            altered,
            context_ref=dict(manifest["implementation_assignment_ref"]),
        )
        with self.assertRaises(PublicClaimGuardError) as payload_error:
            PublicClaimManifestController(self.repository).freeze_manifest(
                manifest,
                transport=mismatched_transport,
                repository_head=self.head,
            )
        self.assertEqual(
            MANIFEST_TRANSPORT_BINDING_MISMATCH,
            payload_error.exception.issue_code,
        )

        receipt_transport = transport_for(
            manifest,
            context_ref=dict(manifest["implementation_assignment_ref"]),
        )
        receipt_transport["transport_receipt"]["receipt_sha256"] = "f" * 64
        with self.assertRaises(PublicClaimGuardError) as receipt_error:
            PublicClaimManifestController(self.repository).freeze_manifest(
                manifest,
                transport=receipt_transport,
                repository_head=self.head,
            )
        self.assertEqual(
            MANIFEST_TRANSPORT_BINDING_MISMATCH,
            receipt_error.exception.issue_code,
        )
        self.assertFalse(
            any(
                record.get("object_id") == manifest["object_id"]
                for record in self.native.store.read_records()
            )
        )

    def test_all_allow_issues_hash_bound_receipt_and_evaluate_is_read_only(
        self,
    ) -> None:
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-allow",
            surface_id="public-surface-allow",
        )
        public, readback = self.freeze(manifest)
        event_path = self.native.store.events_path
        before = event_path.read_bytes()
        span = manifest["spans"][0]
        packet = evaluation_packet(
            manifest,
            event_chain_head=str(readback["event_chain_head"]),
            evidence=[
                evidence_for(
                    span,
                    repository_head=self.head,
                    event_chain_head=str(readback["event_chain_head"]),
                )
            ],
        )
        result = public.evaluate(packet)
        self.assertEqual(ALLOW, result["aggregate_disposition"])
        self.assertEqual("AUTHORIZED", result["authorization_status"])
        self.assertEqual(
            result["decision_hash"],
            result["authorization_receipt"]["decision_hash"],
        )
        self.assertEqual(before, event_path.read_bytes())

    def test_each_evaluate_uses_a_fresh_native_controller(self) -> None:
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-fresh",
            surface_id="public-surface-fresh",
        )
        _, readback = self.freeze(manifest)
        span = manifest["spans"][0]
        packet = evaluation_packet(
            manifest,
            event_chain_head=str(readback["event_chain_head"]),
            evidence=[
                evidence_for(
                    span,
                    repository_head=self.head,
                    event_chain_head=str(readback["event_chain_head"]),
                )
            ],
        )
        calls: list[Path] = []

        def factory(repository: Path) -> IntelligenceTransplantController:
            calls.append(repository)
            return IntelligenceTransplantController(repository)

        public = PublicClaimManifestController(
            self.repository,
            controller_factory=factory,
        )
        public.evaluate(packet)
        public.evaluate(packet)
        self.assertGreaterEqual(len(calls), 2)

    def test_native_predicate_uses_current_projection_and_exact_e3_boundary(
        self,
    ) -> None:
        predicate = {
            "current_gate_equals": "GO",
            "delta_state_equals": "CANDIDATE",
            "execution_status_equals": "ACTIVE",
            "generalized_boundary_equals": GENERALIZED_BOUNDARY,
            "missing_evidence_exact": ["E4_IMPLEMENTATION_BINDING"],
            "object_type_requirements": [
                {
                    "object_type": "E3_ACCEPTED_DISCOVERY",
                    "presence": "PRESENT",
                },
                {
                    "object_type": "E4_IMPLEMENTATION_BINDING",
                    "presence": "ABSENT",
                },
            ],
        }
        text = "The result remains structurally candidate."
        span = claim_span(
            surface_id="graph-surface-001",
            text=text,
            category="BOUNDARY_STATEMENT",
            evidence_type="STAGE5_OBJECT_BUNDLE",
            verification_mode="NATIVE_GRAPH_PREDICATE",
            predicate=predicate,
            maturity="CANDIDATE",
        )
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            surface_id="graph-surface-001",
            text=text,
            span=span,
            object_id="public-claim-manifest-graph",
        )
        public, readback = self.freeze(manifest)
        packet = evaluation_packet(
            manifest,
            event_chain_head=str(readback["event_chain_head"]),
            evidence=[],
        )
        result = public.evaluate(packet)
        self.assertEqual(ALLOW, result["aggregate_disposition"])

        changed = deepcopy(packet)
        changed["evaluation_id"] = "public-evaluation-002"
        stored = self.native.store.read_records()
        e3 = stored[graph_index(stored, E3_ACCEPTED_DISCOVERY)]
        self.assertEqual(GENERALIZED_BOUNDARY, e3["claim_boundary"])
        changed["generalized_boundary"] = GENERALIZED_BOUNDARY
        with self.assertRaises(PublicClaimGuardError) as caught:
            public.evaluate(changed)
        self.assertEqual(RUNTIME_OVERRIDE_ATTEMPT, caught.exception.issue_code)

    def test_historical_graph_contradiction_blocks_without_receipt(self) -> None:
        predicate = {
            "current_gate_equals": "HOLD",
            "delta_state_equals": "NONE",
            "execution_status_equals": "NOT_ESTABLISHED",
            "generalized_boundary_equals": None,
            "missing_evidence_exact": ["E1_DISCOVERY"],
            "object_type_requirements": [],
        }
        text = "Execution is not established and the Gate remains HOLD."
        span = claim_span(
            surface_id="historical-surface-001",
            text=text,
            category="FORMAL_RUN_MATURITY",
            evidence_type="STAGE5_OBJECT_BUNDLE",
            verification_mode="NATIVE_GRAPH_PREDICATE",
            predicate=predicate,
        )
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            surface_id="historical-surface-001",
            text=text,
            span=span,
            object_id="public-claim-manifest-historical",
        )
        public, readback = self.freeze(manifest)
        result = public.evaluate(
            evaluation_packet(
                manifest,
                event_chain_head=str(readback["event_chain_head"]),
                evidence=[],
            )
        )
        self.assertEqual(BLOCK, result["aggregate_disposition"])
        self.assertIn(NATIVE_GRAPH_CONTRADICTION, result["issue_codes"])
        self.assertIsNone(result["authorization_receipt"])

    def test_forbidden_positive_blocks_and_negative_boundary_does_not(
        self,
    ) -> None:
        positive = "generalized transplant established"
        positive_manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            surface_id="positive-surface-001",
            text=positive,
            span=claim_span(
                surface_id="positive-surface-001",
                text=positive,
            ),
            object_id="public-claim-manifest-positive",
        )
        public, readback = self.freeze(positive_manifest)
        span = positive_manifest["spans"][0]
        result = public.evaluate(
            evaluation_packet(
                positive_manifest,
                event_chain_head=str(readback["event_chain_head"]),
                evidence=[
                    evidence_for(
                        span,
                        repository_head=self.head,
                        event_chain_head=str(readback["event_chain_head"]),
                    )
                ],
            )
        )
        self.assertEqual(BLOCK, result["aggregate_disposition"])
        self.assertIn(
            VISIBLE_SPAN_FORBIDDEN_DECLARATION,
            result["issue_codes"],
        )

        negative = "generalized transplant not established"
        negative_manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            surface_id="negative-surface-001",
            text=negative,
            span=claim_span(
                surface_id="negative-surface-001",
                text=negative,
            ),
            object_id="public-claim-manifest-negative",
        )
        public, readback = self.freeze(negative_manifest)
        negative_span = negative_manifest["spans"][0]
        negative_result = public.evaluate(
            evaluation_packet(
                negative_manifest,
                event_chain_head=str(readback["event_chain_head"]),
                evidence=[
                    evidence_for(
                        negative_span,
                        repository_head=self.head,
                        event_chain_head=str(readback["event_chain_head"]),
                    )
                ],
            )
        )
        self.assertEqual(ALLOW, negative_result["aggregate_disposition"])

    def test_r13_documentary_only_holds_and_exact_behavior_allows(self) -> None:
        claim_id = "V13-S5-FR-001-README-DRAFT-000-CLAIM-012"
        text = (
            "This implementation establishes that Stage 5 records can be "
            "structurally represented, validated, stored, linked, and reduced "
            "under the documented manual-authority boundary."
        )
        span = claim_span(
            surface_id="r13-surface-001",
            text=text,
            claim_id=claim_id,
            category="OPERATIONAL_CAPABILITY",
            evidence_type="BEHAVIORAL_TRACE",
            verification_mode="ADVERSARIAL_BEHAVIOR_TEST",
            observed_behavior=(
                "Stage 5 record validation, storage, linking, and reduction "
                "execute at the bound implementation boundary."
            ),
            boundary_id="V13-S5-FR-001-R13-OPERATIONAL-BOUNDARY-001",
        )
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            surface_id="r13-surface-001",
            text=text,
            span=span,
            object_id="public-claim-manifest-r13",
        )
        public, readback = self.freeze(manifest)
        documentary = evidence_for(
            span,
            repository_head=self.head,
            event_chain_head=str(readback["event_chain_head"]),
            evidence_type="DOCUMENTATION_BLOB",
            verification_mode="DOCUMENTARY_BLOB_MATCH",
        )
        documentary_result = public.evaluate(
            evaluation_packet(
                manifest,
                event_chain_head=str(readback["event_chain_head"]),
                evidence=[documentary],
            )
        )
        self.assertEqual(HOLD, documentary_result["aggregate_disposition"])
        self.assertIsNone(documentary_result["authorization_receipt"])

        behavioral = evidence_for(
            span,
            repository_head=self.head,
            event_chain_head=str(readback["event_chain_head"]),
        )
        behavioral_result = public.evaluate(
            evaluation_packet(
                manifest,
                event_chain_head=str(readback["event_chain_head"]),
                evidence=[behavioral],
            )
        )
        self.assertEqual(ALLOW, behavioral_result["aggregate_disposition"])

    def test_fixed_reddit_title_documentary_evidence_allows_with_none_maturity(
        self,
    ) -> None:
        title = (
            "**I built a bounded process for turning one AI-agent failure "
            "into a reusable control**"
        )
        span = claim_span(
            surface_id="reddit-title-surface-001",
            text=title,
            claim_id="V13-S5-FR-001-REDDIT-DRAFT-000-CLAIM-001",
        )
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            surface_id="reddit-title-surface-001",
            text=title,
            span=span,
            object_id="public-claim-manifest-reddit-title",
        )
        public, readback = self.freeze(manifest)
        result = public.evaluate(
            evaluation_packet(
                manifest,
                event_chain_head=str(readback["event_chain_head"]),
                evidence=[
                    evidence_for(
                        span,
                        repository_head=self.head,
                        event_chain_head=str(readback["event_chain_head"]),
                    )
                ],
            )
        )
        self.assertEqual("NONE", span["required_formal_run_maturity"])
        self.assertEqual(ALLOW, result["aggregate_disposition"])

    def test_current_inventory_excludes_superseded_revoked_and_cross_run(
        self,
    ) -> None:
        manifest = manifest_for(self.graph, repository_head=self.head)
        replacement = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-002",
            supersedes=exact_ref(manifest),
        )
        cross_run = deepcopy(replacement)
        cross_run["object_id"] = "cross-run-manifest"
        cross_run["manifest_id"] = "cross-run-manifest"
        cross_run["run_id"] = "other-run"
        cross_run["supersedes"] = None
        cross_run = object_with_content_hash(cross_run)
        inventory = current_object_inventory(
            [*self.graph, manifest, replacement, cross_run],
            run_id=str(self.graph[0]["run_id"]),
        )
        keys = {exact_ref(record)["object_id"] for record in inventory}
        self.assertNotIn(manifest["object_id"], keys)
        self.assertIn(replacement["object_id"], keys)
        self.assertNotIn(cross_run["object_id"], keys)

        revocation = {
            "object_type": "MANUAL_CONTROL_RECEIPT",
            "control_action": "REVOKE",
            "target_object_id": replacement["object_id"],
            "target_content_hash": replacement["content_hash"],
            "run_id": self.graph[0]["run_id"],
        }
        revoked_inventory = current_object_inventory(
            [*self.graph, replacement, revocation],
            run_id=str(self.graph[0]["run_id"]),
        )
        self.assertNotIn(
            replacement["object_id"],
            {record["object_id"] for record in revoked_inventory},
        )

    def test_sidecar_replacement_is_forward_only_and_branching_fails(self) -> None:
        original = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-lineage-001",
            surface_id="public-lineage-surface",
        )
        first = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-lineage-002",
            surface_id="public-lineage-surface",
            supersedes=exact_ref(original),
        )
        branch = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-lineage-003",
            surface_id="public-lineage-surface",
            supersedes=exact_ref(original),
        )
        assessment = validate_graph([*self.graph, original, first, branch])
        self.assertIn("SUPERSESSION_BRANCH", assessment.issue_codes)
        self.assertIn("FORWARD_REPLACEMENT_REQUIRED", assessment.issue_codes)

    def test_missing_exact_current_e3_holds_without_write(self) -> None:
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-missing-e3",
            surface_id="public-surface-missing-e3",
        )
        missing_ref = {
            "object_id": "missing-e3",
            "content_hash": "f" * 64,
        }
        manifest["e3_ref"] = missing_ref
        descriptor = manifest["evidence_catalog"][0]
        descriptor["e3_ref"] = missing_ref
        descriptor["descriptor_hash"] = ""
        descriptor["descriptor_hash"] = hashlib.sha256(
            canonical_json(descriptor)
        ).hexdigest()
        manifest = object_with_content_hash(manifest)
        self.assertTrue(validate_object(manifest).valid)
        with self.assertRaises(PublicClaimGuardError) as caught:
            PublicClaimManifestController(self.repository).freeze_manifest(
                manifest,
                transport=transport_for(
                    manifest,
                    context_ref=dict(
                        manifest["implementation_assignment_ref"]
                    ),
                ),
                repository_head=self.head,
            )
        self.assertEqual(HOLD, caught.exception.disposition)
        self.assertEqual(
            NATIVE_GRAPH_EVIDENCE_UNAVAILABLE,
            caught.exception.issue_code,
        )

    def test_evidence_type_mode_behavior_boundary_and_payload_are_exact(
        self,
    ) -> None:
        manifest = manifest_for(
            self.graph,
            repository_head=self.head,
            object_id="public-claim-manifest-evidence",
            surface_id="public-surface-evidence",
        )
        public, readback = self.freeze(manifest)
        span = manifest["spans"][0]
        event_head = str(readback["event_chain_head"])
        base = evidence_for(
            span,
            repository_head=self.head,
            event_chain_head=event_head,
        )
        mutations = (
            ("evidence_type", "SOURCE_BLOB"),
            ("verification_mode", "SOURCE_BLOB_MATCH"),
            ("boundary_id", "wrong-boundary"),
            ("observed_behavior", "unexpected behavior"),
        )
        for index, (field, changed_value) in enumerate(mutations, start=1):
            evidence = deepcopy(base)
            evidence[field] = changed_value
            packet = evaluation_packet(
                manifest,
                event_chain_head=event_head,
                evidence=[evidence],
            )
            packet["evaluation_id"] = f"public-evidence-mismatch-{index}"
            result = public.evaluate(packet)
            self.assertEqual(BLOCK, result["aggregate_disposition"])
            self.assertIn(
                EVIDENCE_APPLICABILITY_MISMATCH,
                result["issue_codes"],
            )
            self.assertIsNone(result["authorization_receipt"])

        payload_mismatch = deepcopy(base)
        payload = b"different exact evidence bytes"
        payload_mismatch["payload_base64"] = base64.b64encode(payload).decode(
            "ascii"
        )
        payload_mismatch["payload_sha256"] = hashlib.sha256(payload).hexdigest()
        result = public.evaluate(
            evaluation_packet(
                manifest,
                event_chain_head=event_head,
                evidence=[payload_mismatch],
            )
        )
        self.assertEqual(BLOCK, result["aggregate_disposition"])
        self.assertIn(EVIDENCE_APPLICABILITY_MISMATCH, result["issue_codes"])

    def test_cli_intercepts_before_authorization_output(self) -> None:
        packet_path = self.root / "evaluation.json"
        packet_path.write_text("{}", encoding="utf-8")
        output = StringIO()
        with patch(
            "decision_os.cli.PublicClaimManifestController.evaluate",
            side_effect=PublicClaimGuardError(
                BLOCK,
                RUNTIME_OVERRIDE_ATTEMPT,
                "blocked before authorization",
            ),
        ):
            exit_code = cli_main(
                ["public-claim", str(self.repository), str(packet_path)],
                stdout=output,
                stderr=StringIO(),
            )
        self.assertEqual(5, exit_code)
        payload = json.loads(output.getvalue())
        self.assertEqual("NOT_AUTHORIZED", payload["authorization_status"])
        self.assertIsNone(payload["authorization_receipt"])


if __name__ == "__main__":
    unittest.main()
