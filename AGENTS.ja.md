# AGENTS.ja.md — Decision-OS V13 日本語入口

## 何のためか

良い完了は、次回のAIコストを下げる。良いループは、一生のAIコストを下げる。

これは、AI coding session のあとに、AI が “done” と言っても、次の実行でまた文脈回収に tokens を使ってしまう問題を減らすための入口です。

V12 / V13 は、AI に「終わったか」だけでなく、「次を走らせてよいか」まで短く報告させます。

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
