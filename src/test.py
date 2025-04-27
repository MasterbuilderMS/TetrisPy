text = '''Eiqhztk 2: Zit Hqofztr Iqss
Stfq’l ysqlisouiz ysoeatktr, zitf lztqrotr. Lit vql lzqfrofu of q sgfu egkkorgk softr vozi dxkqsl -- lzkqfut, lxkktqs hqofzoful gy kgwtr youxktl, odhgllowst sqfrleqhtl, qfr rggkl voziof rggkl. Tqei gft iqr zit lqdt lndwgs: q eokest vozi qf B.

Ql lit dgctr rtthtk, q ixddofu lgxfr yosstr zit qok -- sgv qfr kinzidoe, soat q rolzqfz eiqfz. Itk yofutkl wkxlitr gft gy zit dxkqsl. Oz vql vqkd.

Zitf lit itqkr oz. Q cgoet. Fgz sgxr, fgz estqk. Pxlz q violhtk:
“Ngx ligxsrf’z wt itkt.”

Lit lhxf qkgxfr. Fg gft.

Zit eiqfz uktv sgxrtk. Zit hqofzoful lttdtr zg lioyz vitf lit vqlf’z sggaofu roktezsn qz zitd.

Qz zit tfr gy zit iqss, q zqss qkeitr rggkvqn lzggr ghtf. Wtngfr oz: rqkaftll. Wxz lgdtziofu usgvtr oflort -- q wsxt, ysoeatkofu souiz.

Lit lzthhtr zikgxui.

Qfr eqdt yqet-zg-yqet vozi lgdtgft vig sggatr tbqezsn soat itk.
'''.lower()

a, b = input("> ").split()
for c in range(len(a)):
    text = text.replace(a[c],b[c])

print(text)