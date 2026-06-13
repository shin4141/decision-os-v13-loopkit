# AGENTS.ja.md — Decision-OS V13 日本語入口

## 何のためか

良い完了は、次回のAIコストを下げる。良いループは、一生のAIコストを下げる。

これは、AI coding session のあとに、AI が “done” と言っても、次の実行でまた文脈回収に tokens を使ってしまう問題を減らすための入口です。

V12 / V13 は、AI に「終わったか」だけでなく、「次を走らせてよいか」まで短く報告させます。

## 最小運用ロジック

大きく進めず、次の安全な0.01だけを選びます。

不確実なときは、実装ではなく確認・記録・整理を次の一手にします。

1.00を狙って壊すより、0.01を確実に積みます。

作業は、ownerの目的線 / Aspire を守るために行います。

目的線を壊す変更、回復不能な変更、owner承認外の変更は進めません。

判断に迷ったら、速く進むことより、次回も再開できることを優先します。

実装前に touch surface を分けます。

- 触ってよい面
- 触ると壊れる面
- まだ触るな面

他人のrepo、既存product、inherited codeでは特に必須です。

env / DB / deploy / release / schema / public surface は軽く扱いません。

小さな完了を守ります。

UI修正をauth実装へ、bug fixを全面refactorへ、docs修正をproduct変更へ広げません。

広げる場合は、別taskとしてowner approvalを取ります。

完了は「やった」ではなく、変更点・確認結果・残りリスク・次回再開情報で判断します。

次の人間またはAIが迷わず再開できないなら、PASSではなくDELAYに寄せます。

悪い完了は、次回のAIに文脈回収コストを払わせます。

悪いhandoffは、強いmodelにcleanupをさせます。

悪いloopは、将来のAIコストを増やします。

## 判断ロジック最小版

上の運用ロジックで判断したうえで、最後に最小フッターを出させる。フッターだけでは判断基準にならない。

V12 State:

- PASS: 作業が完了し、証拠があり、次回の人間またはAIが再開できる。
- DELAY: 作業は進んだが、確認・証拠・handoff・再開情報が不足している。
- BLOCK: 完了扱いにすると危険、条件不足、または所有者確認なしでは進めない。

V13 Next Loop Gate:

- GO: 次の作業に進んでよい。
- HOLD: 追加確認・待機・文脈整理が必要。
- CAP: 小さな完了を守り、作業を広げない。scope creepを止める。
- BLOCK: 次の作業が危険、曖昧、承認外、または触ってはいけない領域に入る。

## 最小フッター

まずは final report の末尾に、この footer を付けさせます。

```text
V12 State: PASS / DELAY / BLOCK
V13 Next Loop Gate: GO / HOLD / CAP / BLOCK
Reason:
Next Loop:
```

## V12 / V13 の意味

V12 は、その作業が本当に complete か、evidenced か、restartable かを見ます。

V13 は、次の loop を GO / HOLD / CAP / BLOCK のどれにするべきかを見ます。

Reason は、判断の理由を短く書きます。

Next Loop は、次にやる action を一つだけ書きます。

## CAP の意味

CAP は「小さな勝ちは ship する。ただし task を広げない」という意味です。

たとえば、小さな修正が終わったあとに、AI が勝手に redesign、refactor、新機能追加へ進まないようにします。

## 使う場面

- AI coding session のあと
- AI に scope を広げさせる前
- 他人の repo や inherited code を触る前
- 強い model に cleanup させる前
- 「done だけど、次に進んでいいか不安」なとき

## やってはいけないこと

- これを tests や code review の代わりにしない
- owner approval なしに AI に scope を広げさせない
- 既存 repo の rules を勝手に overwrite しない
- env、DB、deploy、release、schema、public surface を軽く扱わない
- PASS や GO を無理に出させない

## Canonical

Canonical rules は `AGENTS.md` にあります。

この `AGENTS.ja.md` は、日本語の entry / guide です。full replacement ではありません。

迷ったら、既存 repo の rules と owner approval を優先してください。
