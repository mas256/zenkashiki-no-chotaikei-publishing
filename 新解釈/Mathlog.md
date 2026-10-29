# 漸化式の新解釈

漸化式を解いていると、定数を引いたり、隣り合う項を組み合わせたり、三角関数で置き換えたりします。

それぞれの計算はできても、なぜその変形を選ぶのかは少し見えにくいところです。行列と複素数を使って、こうした解法のつながりを眺めてみます。

行列の計算・固有値・対角化・極形式は使えるものとして、具体例から始めます。

## 和と差を取るのは、対角化だった

まずは、よくある連立漸化式です。

\begin{align*}
\begin{cases}
x_{n+1}=2x_n+y_n,\\
y_{n+1}=x_n+2y_n.
\end{cases}
\end{align*}

二式の和と差を取ると、

\begin{align*}
x_{n+1}+y_{n+1}&=3(x_n+y_n),\\
x_{n+1}-y_{n+1}&=x_n-y_n.
\end{align*}

和は3倍、差は一定です。初期値が$\displaystyle x_1=1,y_1=0$なら、

\begin{align*}
x_n=\frac{3^{n-1}+1}{2},\qquad
y_n=\frac{3^{n-1}-1}{2}
\end{align*}

と求まります。

ここで$\displaystyle \boldsymbol v_n=(x_n,y_n)^{\mathsf T}$と置き、行列で書くと、

\begin{align*}
\boldsymbol v_{n+1}=A\boldsymbol v_n,\qquad
A=\begin{pmatrix}2&1\\1&2\end{pmatrix}
\end{align*}

です。$\displaystyle A$の固有値は3と1で、対応する固有ベクトルは$\displaystyle (1,1)^{\mathsf T}$と$\displaystyle (1,-1)^{\mathsf T}$。実際、

\begin{align*}
\begin{pmatrix}x_n\\y_n\end{pmatrix}
=\frac{x_n+y_n}{2}\begin{pmatrix}1\\1\end{pmatrix}
+\frac{x_n-y_n}{2}\begin{pmatrix}1\\-1\end{pmatrix}.
\end{align*}

和と差を追うと解けたのは、固有ベクトルを基準にすれば、二つの成分が別々に等比的に変化するからです。高校数学で行う和と差の解法は、この例では対角化を成分ごとに計算していたわけです。

## 隣接3項間漸化式も、連立にする

次に、

\begin{align*}
a_{n+2}=5a_{n+1}-6a_n
\end{align*}

を考えます。隣り合う二項を一組にすれば、

\begin{align*}
\begin{pmatrix}a_{n+2}\\a_{n+1}\end{pmatrix}
=B\begin{pmatrix}a_{n+1}\\a_n\end{pmatrix},\qquad
B=\begin{pmatrix}5&-6\\1&0\end{pmatrix}.
\end{align*}

一つの数列の式が、二成分の連立漸化式になりました。$\displaystyle B$の特性方程式は、いつもの

\begin{align*}
\lambda^2-5\lambda+6=0
\end{align*}

です。根の2と3は、各固有方向での倍率を表します。だから一般項も

\begin{align*}
a_n=C2^{n-1}+D3^{n-1}
\end{align*}

という形になります。例えば$\displaystyle a_1=1,a_2=4$なら、$\displaystyle C=-1,D=2$です。

では、普通の解法で作る$\displaystyle a_{n+1}-2a_n$は何でしょうか。

\begin{align*}
a_{n+2}-2a_{n+1}=3(a_{n+1}-2a_n)
\end{align*}

となるので、これは3倍される成分を取り出しています。行列で書けば、

\begin{align*}
(1,-2)B=3(1,-2).
\end{align*}

固有ベクトルで状態を分ける方法と、一定倍率になる量を組み合わせる方法。二つは、同じ行列を別の側から見た解法です。

## 定数を引くのは、原点を移すため

もっと基本的な

\begin{align*}
a_{n+1}=2a_n+1
\end{align*}

も、この流れに入ります。不動点は$\displaystyle \alpha=2\alpha+1$を解いて$\displaystyle \alpha=-1$。そこからのずれを取れば、

\begin{align*}
a_{n+1}+1=2(a_n+1)
\end{align*}

です。原点を$\displaystyle -1$に移すと、毎回2倍されるだけになります。

定数項のある連立漸化式でも同じです。

\begin{align*}
\boldsymbol v_{n+1}=A\boldsymbol v_n+\boldsymbol b
\end{align*}

に不動点$\displaystyle \boldsymbol v_*$があれば、

\begin{align*}
\boldsymbol v_{n+1}-\boldsymbol v_*
=A(\boldsymbol v_n-\boldsymbol v_*)
\end{align*}

となります。定数を引く解法は、複数の数を同時に追っていてもそのまま使えます。

なお、不動点の値と固有値は役割が違います。不動点は動かない場所、固有値はその方向での倍率です。

## 重解で出てくる「$\displaystyle n$」は、足し算の積み重ね

特性方程式が重解を持つと、一般項に$\displaystyle n$が現れます。例えば、

\begin{align*}
a_{n+2}=4a_{n+1}-4a_n
\end{align*}

の特性多項式は$\displaystyle (X-2)^2$です。ここで$\displaystyle a_n=2^{n-1}b_n$と置くと、

\begin{align*}
b_{n+2}-2b_{n+1}+b_n=0.
\end{align*}

つまり、$\displaystyle b_{n+2}-b_{n+1}=b_{n+1}-b_n$。$\displaystyle b_n$は等差数列なので、

\begin{align*}
a_n=2^{n-1}\{C+D(n-1)\}
\end{align*}

となります。例えば$\displaystyle a_1=1,a_2=4$なら、$\displaystyle a_n=n2^{n-1}$です。

2倍される変化を取り除いたら、一定量を足す変化が残りました。この足し算が$\displaystyle n$の出どころです。

行列でも、対応する二成分の更新を適切な基底で表すと、

\begin{align*}
\begin{pmatrix}c_{n+1}\\d_{n+1}\end{pmatrix}
=\begin{pmatrix}2&1\\0&2\end{pmatrix}
\begin{pmatrix}c_n\\d_n\end{pmatrix}
\end{align*}

という形になります。一方の成分が2倍されながら、もう一方へ毎回寄与するため、その寄与が積み重なります。

ただし、固有値が重なれば必ず$\displaystyle n$が出るわけではありません。例えば$\displaystyle 2I$なら、どの成分もただ2倍されるだけです。ここでは、固有方向が二つ取れず、成分どうしの寄与が残ることが効いています。

## 差を取って、項数を減らす

同じ考え方は、もっと多くの項を結ぶ漸化式にも使えます。

\begin{align*}
a_{n+3}=6a_{n+2}-11a_{n+1}+6a_n
\end{align*}

を差の形にまとめると、

\begin{align*}
&(a_{n+3}-a_{n+2})-5(a_{n+2}-a_{n+1})\\
&\qquad+6(a_{n+1}-a_n)=0.
\end{align*}

$\displaystyle b_n=a_{n+1}-a_n$と置けば、

\begin{align*}
b_{n+2}-5b_{n+1}+6b_n=0
\end{align*}

になり、項数が一つ減ります。

例えば$\displaystyle a_1=1,a_2=2,a_3=6$なら、$\displaystyle b_1=1,b_2=4$。先ほど解いた式と同じなので、

\begin{align*}
b_n=-2^{n-1}+2\cdot3^{n-1}.
\end{align*}

あとは和を取って、

\begin{align*}
a_n&=a_1+\sum_{j=1}^{n-1}b_j\\
&=1-2^{n-1}+3^{n-1}
\end{align*}

と戻せます。$\displaystyle n=1$では和を0とします。

この例で差が有効なのは、特性多項式が

\begin{align*}
X^3-6X^2+11X-6=(X-1)(X-2)(X-3)
\end{align*}

と分かれるからです。普通の差$\displaystyle a_{n+1}-a_n$を作る操作は、因子$\displaystyle X-1$に対応します。

一般には、特性根$\displaystyle r$に合わせて$\displaystyle a_{n+1}-ra_n$を作れば、その因子を一つ取り除けます。$\displaystyle r\ne0$なら、$\displaystyle a_n=r^{n-1}c_n$として

\begin{align*}
a_{n+1}-ra_n=r^n(c_{n+1}-c_n)
\end{align*}

です。いつもの補助数列も、倍率を取り除いた後の差分と見られます。

通常の差分がそのまま有効なのは、1が特性根である場合です。どんな式でも差を取れば項数が減る、というわけではありません。

## 複素数にまとめると、回転が見える

今度は、特性根が非実数になる例です。

\begin{align*}
a_{n+2}=2a_{n+1}-2a_n.
\end{align*}

特性根は$\displaystyle 1\pm i$。ここで、

\begin{align*}
z_n=a_{n+1}-(1-i)a_n
\end{align*}

と置くと、

\begin{align*}
z_{n+1}
&=a_{n+2}-(1-i)a_{n+1}\\
&=(1+i)a_{n+1}-2a_n\\
&=(1+i)z_n.
\end{align*}

先ほどの$\displaystyle a_{n+1}-2a_n$と、やっていることは同じです。今回は倍率が複素数になりました。

$\displaystyle 1+i=\sqrt2e^{i\frac{\pi}{4}}$なので、$\displaystyle z_n$は毎回$\displaystyle \sqrt2$倍されながら、反時計回りに$\displaystyle \frac{\pi}{4}$回転します。

初期値が$\displaystyle a_1=0,a_2=1$なら$\displaystyle z_1=1$なので、

\begin{align*}
z_n=(1+i)^{n-1}.
\end{align*}

また、$\displaystyle z_n=(a_{n+1}-a_n)+ia_n$だから、虚部を読めば

\begin{align*}
a_n=(\sqrt2)^{n-1}\sin\frac{(n-1)\pi}{4}
\end{align*}

です。実数列の一般項に三角関数が現れるのは、その背後で複素数の掛け算が回転を表しているからです。

実数の根もこの見方に含まれます。正の倍率なら回転角0、負の倍率なら回転角$\displaystyle \pi$です。ただし、元の二項を並べた平面で、そのまま円運動に見えるとは限りません。上の$\displaystyle z_n$のように、座標を選び直して回転を見ています。

## 一次分数型は、連立漸化式の比

最初の連立漸化式に戻って、今度は成分の比

\begin{align*}
a_n=\frac{x_n}{y_n}
\end{align*}

だけを追ってみます。すると、

\begin{align*}
a_{n+1}
=\frac{2x_n+y_n}{x_n+2y_n}
=\frac{2a_n+1}{a_n+2}.
\end{align*}

一次分数型になりました。連立漸化式と一次分数型は、こうして同じ行列から作れます。以下、比や更新式の分母が0にならない範囲で考えます。

この例の不動点は1と$\displaystyle -1$です。対応する固有ベクトルは$\displaystyle (1,1)^{\mathsf T}$と$\displaystyle (-1,1)^{\mathsf T}$なので、

\begin{align*}
\begin{pmatrix}x_n\\y_n\end{pmatrix}
=c_n\begin{pmatrix}1\\1\end{pmatrix}
+d_n\begin{pmatrix}-1\\1\end{pmatrix}
\end{align*}

と分けると、$\displaystyle c_{n+1}=3c_n,d_{n+1}=d_n$です。一方、

\begin{align*}
\frac{a_n-1}{a_n+1}
=\frac{x_n-y_n}{x_n+y_n}
=-\frac{d_n}{c_n}.
\end{align*}

だから、この比は毎回$\displaystyle \frac13$倍されます。一次分数型で使う「二つの不動点からの差の比」は、二つの固有方向の成分比を取り出していたのです。

一般の

\begin{align*}
f(a)=\frac{pa+q}{ra+s},\qquad
M=\begin{pmatrix}p&q\\r&s\end{pmatrix}
\end{align*}

でも、不動点$\displaystyle \alpha$について

\begin{align*}
M\begin{pmatrix}\alpha\\1\end{pmatrix}
=(r\alpha+s)\begin{pmatrix}\alpha\\1\end{pmatrix}.
\end{align*}

不動点は固有ベクトルの成分比で、対応する固有値は$\displaystyle \lambda_\alpha=r\alpha+s$です。

$\displaystyle r\ne0,ps-qr\ne0$とし、異なる二つの不動点を$\displaystyle \alpha,\beta$とすると、差の比は

\begin{align*}
\frac{a_{n+1}-\alpha}{a_{n+1}-\beta}
=\frac{\lambda_\beta}{\lambda_\alpha}
\frac{a_n-\alpha}{a_n-\beta}
\end{align*}

を満たします。公比が固有値の比になるところまで、連立漸化式から説明できます。初項が不動点なら、定数列として先に扱えば十分です。

不動点が重なる場合にも、重解とのつながりがあります。例えば、

\begin{align*}
a_{n+1}=\frac{4a_n-9}{a_n-2}
\end{align*}

の不動点は3だけで、$\displaystyle a_n\ne3$なら、

\begin{align*}
\frac1{a_{n+1}-3}=\frac1{a_n-3}+1.
\end{align*}

ここでも一定量の足し算が残ります。対応する行列の固有値は重解1で、先ほどの重解の話が、今度は成分比に現れています。

## 一つの行列を、三通りに見る

最後に、行列・複素数・一次分数型がそろう例を見てみます。

\begin{align*}
\begin{pmatrix}x_{n+1}\\y_{n+1}\end{pmatrix}
=\begin{pmatrix}1&1\\-1&1\end{pmatrix}
\begin{pmatrix}x_n\\y_n\end{pmatrix}.
\end{align*}

$\displaystyle z_n=y_n+ix_n$とまとめれば、

\begin{align*}
z_{n+1}=(1+i)z_n.
\end{align*}

毎回$\displaystyle \sqrt2$倍されながら、$\displaystyle \frac{\pi}{4}$回転します。各成分は、先ほどの隣接3項間漸化式

\begin{align*}
x_{n+2}=2x_{n+1}-2x_n
\end{align*}

を満たします。

一方、$\displaystyle a_n=\frac{x_n}{y_n}$だけを記録すると、

\begin{align*}
a_{n+1}=\frac{a_n+1}{1-a_n}.
\end{align*}

不動点は$\displaystyle i,-i$なので、$\displaystyle b_n=\frac{a_n-i}{a_n+i}$と置けば、

\begin{align*}
b_{n+1}=ib_n.
\end{align*}

実数$\displaystyle a_n$に対して$\displaystyle |b_n|=1$ですから、こちらは単位円上の$\displaystyle \frac{\pi}{2}$回転です。

回転角が2倍なのは、$\displaystyle a=\tan\theta$とすると、

\begin{align*}
\frac{a-i}{a+i}=-e^{2i\theta}
\end{align*}

となるためです。傾きは$\displaystyle \theta$と$\displaystyle \theta+\pi$を区別しないので、円周上では角度を2倍して記録しています。

例えば$\displaystyle a_1=\frac12$なら、

\begin{align*}
\frac12,\quad3,\quad-2,\quad-\frac13,\quad\frac12,\ldots
\end{align*}

という4周期になります。どの項も1ではないので、更新も続けられます。

元の行列を$\displaystyle M$とすると、$\displaystyle M^4=-4I$です。四回後のベクトルは元には戻りませんが、両成分が同じ倍率を受けるので、比は元に戻ります。状態全体の周期と、成分比の周期は同じとは限りません。

なお、円周上で回転できても、実数列が必ず続くとは限りません。同じ式でも$\displaystyle a_1=0$なら$\displaystyle a_2=1$となり、$\displaystyle a_3$は定義できません。成分比で表せなくなる点があるためです。

## おまけ：角度を倍にする漸化式

回転の話と似ているものに、

\begin{align*}
a_{n+1}=2a_n^2-1
\end{align*}

があります。$\displaystyle a_1=\cos\theta$なら、倍角公式から

\begin{align*}
a_n=\cos(2^{n-1}\theta).
\end{align*}

ただし、こちらは一定角の回転ではありません。複素数で表せば、

\begin{align*}
z_{n+1}=z_n^2
\end{align*}

という角度を倍にする更新です。一定数を掛ける式と、二乗する式では、同じ単位円を使っていても動きが違います。

整数倍角まで広げれば、チェビシェフ多項式の$\displaystyle T_d(\cos\theta)=\cos(d\theta)$から、

\begin{align*}
a_{n+1}=T_d(a_n)
\quad\Longrightarrow\quad
a_n=\cos(d^{n-1}\theta)
\end{align*}

も得られます。ここでは$\displaystyle d\ge2$を固定した整数とし、$\displaystyle a_1=\cos\theta$としています。

---

和と差を作る、不動点を引く、隣り合う項をまとめる、成分の比を取る。こうした変形を行列と複素数で見ると、別々に覚えていた解法のつながりが見えてきます。

一般項を求めた後に、その式がどんな動きを記録しているのか考えてみると、同じ漸化式も少し違って見えるかもしれません。
