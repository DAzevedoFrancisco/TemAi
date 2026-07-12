"""
Gera o PDF do guia de utilização da plataforma Mob.
Uso: python scripts/generate_user_guide_pdf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PDF = ROOT / "docs" / "guia-utilizacao-mob.pdf"
OUTPUT_MD = ROOT / "docs" / "guia-utilizacao-mob.md"

FONT_DIR = Path(r"C:\Windows\Fonts")
FONT_REGULAR = FONT_DIR / "arial.ttf"
FONT_BOLD = FONT_DIR / "arialbd.ttf"
FONT_ITALIC = FONT_DIR / "ariali.ttf"


def build_sections() -> list[tuple[str, int, str]]:
    """Return list of (title, level, body). level: 0=skip, 1=chapter, 2=section."""
    return [
        (
            "Olá! Bem-vindo à Mob",
            1,
            "Imagina que estou ao teu lado a mostrar-te a plataforma. A Mob é um site feito para a cidade da "
            "Beira: de um lado estão as pessoas que procuram produtos e lojas; do outro, quem tem negócio e "
            "quer divulgar o que vende.\n\n"
            "Não precisas de perceber termos técnicos. Pensa só nisto: entras no site, pesquisas o que "
            "queras — perfume, comida, o que for — e o sistema mostra-te quem vende isso perto de ti. "
            "Se fores dono de loja, também podes registar o teu estabelecimento e pôr os teus produtos online.\n\n"
            "Há três formas de usar a Mob:\n\n"
            "Como cliente, só procuras e descobres.\n"
            "Como vendedor, geres a tua loja e o teu catálogo.\n"
            "Como administrador, cuidas de toda a plataforma — mas isso só quem a equipa autorizar é que tem.",
        ),
        (
            "Primeiro passo: criar conta",
            1,
            "Se ainda não tens conta, é por aqui que se começa.\n\n"
            "Abre o site e clica em «Entrar», no canto superior. Vais ver dois separadores: «Entrar» e "
            "«Cadastrar». Escolhe «Cadastrar».\n\n"
            "O formulário pede o básico: o teu nome completo (pelo menos 6 letras), data de nascimento, "
            "sexo, email e uma senha. O email tem de ser teu e não pode já estar registado por outra pessoa. "
            "Para criar conta precisas de ter pelo menos 14 anos.\n\n"
            "Quando carregas em «Criar conta», o sistema trata de tudo: cria o teu utilizador, mete-te "
            "automaticamente como cliente e já te deixa entrar. Não precisas de fazer mais nada — vais parar "
            "à página inicial, pronto para pesquisar.\n\n"
            "Uma coisa importante: criar conta não te torna vendedor nem administrador. Isso são passos "
            "à parte, que já explico mais abaixo.",
        ),
        (
            "Já tens conta? Então faz login",
            1,
            "Na mesma página (/auth/), fica no separador «Entrar». Mete o email e a senha que usaste no "
            "cadastro e confirma.\n\n"
            "Se estiver tudo certo, entras logo. Para onde vais depende do teu papel:\n\n"
            "Se és cliente ou vendedor, vais para a página inicial — aquela com «O Que Procura?» no meio.\n"
            "Se és administrador, vais directo para o painel de gestão em /gestao/.\n\n"
            "Se te enganares na senha, o site avisa-te. Não há mistério.\n\n"
            "Para sair, clica em «Sair» no menu. Aparece uma confirmação — é de propósito, para não "
            "fechares a sessão sem querer. Depois de confirmar, voltas à página de login.",
        ),
        (
            "Usar a Mob como cliente",
            1,
            "Isto é o que a maioria das pessoas faz. Entras, pesquisas, vês resultados, e se gostares de "
            "algo abres o detalhe para saber onde comprar.\n\n"
            "Na página inicial escreves o que procuras — por exemplo «Inuka» ou «perfume» — e carregas na "
            "seta ou no Enter. Saltas para a página de resultados.\n\n"
            "Lá em cima vês quantos produtos encontrou. Podes filtrar por categoria: «Todas», «Saúde e "
            "Beleza», e outras que aparecerem conforme a pesquisa.\n\n"
            "Repara no botão «Usar minha localização». Se clicares, o browser pede permissão para saber "
            "onde estás. Se aceitares, a Mob passa a mostrar a distância até cada loja — em linha recta, "
            "não é tempo de viagem, mas dá uma boa ideia do que está perto. Depois disso também podes "
            "filtrar por raio: 2 km, 5 km, 10 km ou 25 km.\n\n"
            "Cada cartão de produto mostra a foto, a categoria, se está disponível, o nome da loja e a "
            "morada. Clica num cartão para abrir o detalhe completo.",
        ),
        (
            "O detalhe do produto — o que vais ver",
            2,
            "Esta página é onde decides se vale a pena ir à loja.\n\n"
            "Vês a imagem grande, o nome, a descrição, e badges a dizer a categoria e se o produto está "
            "disponível ou não. Há um bloco com o nome do estabelecimento — tipo «Aroma da Rosch» — e a "
            "indicação de que fica na Beira.\n\n"
            "Mais abaixo tens os dados práticos: morada exacta, telefone (podes clicar para ligar) e "
            "horário de funcionamento. Há um botão para contactar directamente.\n\n"
            "Do lado direito (ou em baixo no telemóvel) tens um mapa com um pin na localização da loja. "
            "Se vieste da pesquisa com GPS activo, também aparece quantos quilómetros estás, em linha recta.\n\n"
            "Há ainda uma secção de avaliações — comentários e estrelas de outros clientes. Podes ler o "
            "que dizem sobre a loja antes de ir.",
        ),
        (
            "Favoritos e avaliações — mas tens de estar logado",
            2,
            "Algumas coisas só funcionam com sessão iniciada.\n\n"
            "Favoritos: no detalhe do produto há um coração. Clicas e o produto fica guardado. Depois "
            "vais ao menu «Favoritos» e vês tudo o que guardaste. Clicas outra vez no coração para tirar.\n\n"
            "Avaliações: na mesma página de detalhe, mais em baixo, podes dar estrelas e/ou escrever um "
            "comentário sobre o estabelecimento. Podes enviar só estrelas, só texto, ou os dois. E podes "
            "actualizar a tua avaliação mais tarde se mudares de opinião.\n\n"
            "Há uma regra justa: não podes favoritar nem avaliar os teus próprios produtos. Se fores "
            "vendedor e tiveres loja na plataforma, isso aplica-se aos teus negócios. Faz sentido — "
            "não avalias o teu próprio serviço.",
        ),
        (
            "O que podes e o que não podes fazer como cliente",
            2,
            "Podes:\n"
            "— Pesquisar à vontade, com ou sem localização.\n"
            "— Ver tudo o que está público: produtos activos de lojas activas.\n"
            "— Guardar favoritos e deixar comentários (excepto nos teus próprios negócios).\n"
            "— Ler os termos e a política de privacidade no site.\n"
            "— Pedir para te tornares vendedor, se tiveres 18 anos ou mais.\n\n"
            "Não podes:\n"
            "— Entrar no painel de vendedor sem ter activado esse papel.\n"
            "— Entrar em /gestao/ — isso é só para administradores.\n"
            "— Criar ou apagar lojas e produtos.\n"
            "— Bloquear outras contas.\n"
            "— Pesquisar com o campo vazio — não devolve nada, tens de escrever alguma coisa.\n"
            "— Ver lojas ou produtos que foram bloqueados pela administração.",
        ),
        (
            "Queres vender? Torna-te vendedor",
            1,
            "Se tens um negócio na Beira e queres aparecer na Mob, o caminho começa no menu: «Tornar-me "
            "vendedor». Só aparece se ainda não fores vendedor.\n\n"
            "Precisas de estar com sessão iniciada e de ter pelo menos 18 anos. Se fores mais novo, o "
            "sistema bloqueia e explica porquê — não é personal, é regra da plataforma.\n\n"
            "Confirmas na janelinha que aparece e pronto: ganhas o papel de vendedor, mas continuas "
            "cliente também. Não perdes nada do que já tinhas.\n\n"
            "Na primeira vez, o site leva-te a criar o teu primeiro estabelecimento. Faz sentido — "
            "sem loja registada, não há onde pôr produtos.",
        ),
        (
            "O painel do vendedor — o teu escritório online",
            1,
            "Depois de seres vendedor, no menu aparece «Painel vendedor» em vez de «Tornar-me vendedor». "
            "Clicas e entras no dashboard em /vendedor/dashboard/.\n\n"
            "É uma área diferente da parte pública do site. Tens menu lateral com Dashboard, "
            "Estabelecimentos, e acesso aos comentários. No topo vês o teu nome e um sino — quando "
            "alguém deixa avaliação nas tuas lojas, aparece ali para não perderes nada.\n\n"
            "Uma coisa a notar: quando estás em «modo vendedor», a pesquisa da página inicial fica "
            "escondida. Não é bug — é para não misturares gerir loja com procurar produtos. Se quiseres "
            "voltar a pesquisar como cliente, mudas para o perfil Cliente (há um botão na home ou podes "
            "usar o link de mudança de perfil).",
        ),
        (
            "Registar e cuidar da tua loja",
            2,
            "Vai a Estabelecimentos e clica em criar novo. Preenches o nome da loja, morada, telefone "
            "(tem de ser número moçambicano, tipo 82, 83, 84…) e o horário de funcionamento.\n\n"
            "A parte mais importante é o mapa: tens de marcar onde a loja fica, e tem de ser dentro da "
            "cidade da Beira. O sistema valida isso — se puseres o pin fora da área, não deixa guardar.\n\n"
            "Depois de criar, podes sempre editar. Mas só as tuas lojas; as dos outros vendedores nem "
            "aparecem no teu painel.",
        ),
        (
            "Produtos — o teu catálogo",
            2,
            "Dentro de cada estabelecimento entras na lista de produtos. Crias um novo com nome, "
            "descrição, categoria e foto — a imagem é obrigatória na criação.\n\n"
            "Marcas se está disponível ou indisponível. Um produto indisponível ainda pode aparecer na "
            "pesquisa, mas fica marcado como tal — útil quando acabou stock mas queres manter o anúncio.\n\n"
            "Podes editar, apagar, ou só mudar a disponibilidade sem apagar. Há também uma pesquisa "
            "interna na lista, para quando tiveres muitos produtos.\n\n"
            "Lembra-te: só mexes nos produtos das tuas lojas. Tentar aceder ao produto de outro vendedor "
            "pelo URL não funciona — o sistema devolve erro.",
        ),
        (
            "Comentários — o que os clientes dizem de ti",
            2,
            "Quando alguém avalia o teu estabelecimento, recebes notificação no sino. Na área de "
            "comentários vês tudo: quem comentou, quantas estrelas, o texto.\n\n"
            "Podes marcar como lido para organizares. E podes moderar: aprovar ou rejeitar avaliações "
            "nas tuas lojas. Isto dá-te algum controlo sobre o que fica visível publicamente.\n\n"
            "Também podes ver comentários separados por estabelecimento, se tiveres mais do que uma loja.",
        ),
        (
            "O que podes e o que não podes fazer como vendedor",
            2,
            "Podes tudo o que um cliente pode — pesquisar, ver detalhes, etc. — mais:\n"
            "— Criar e editar os teus estabelecimentos.\n"
            "— Gerir produtos: criar, editar, apagar, mudar disponibilidade.\n"
            "— Ver e responder a comentários dos teus negócios.\n"
            "— Alternar entre modo cliente e modo vendedor.\n\n"
            "Não podes:\n"
            "— Mexer nas lojas ou produtos de outra pessoa.\n"
            "— Registar estabelecimento fora da Beira.\n"
            "— Tornar-te vendedor com menos de 18 anos.\n"
            "— Entrar no painel de administração.\n"
            "— Avaliar ou favoritar os teus próprios produtos.\n"
            "— Bloquear utilizadores — isso é trabalho do administrador.",
        ),
        (
            "O administrador — quem cuida de tudo",
            1,
            "Este papel não se pede no site. Alguém que já é administrador é que te promove, ou então "
            "crias a conta via comando técnico no servidor (createsuperuser) — isso é coisa de quem "
            "instala o sistema.\n\n"
            "Quando és administrador, o login leva-te directo para /gestao/. O menu público mostra "
            "«Administração» em vez de favoritos ou painel vendedor.\n\n"
            "Importante: quando te tornam administrador, perdes os papéis de cliente e vendedor na "
            "base de dados. Ficas só administrador. Ainda podes abrir as páginas públicas manualmente, "
            "mas o teu trabalho principal é o painel de gestão.",
        ),
        (
            "O que fazes no painel de gestão",
            2,
            "No dashboard vês números gerais: quantos utilizadores, lojas, produtos, quantos activos, "
            "quantos bloqueados. É a fotografia da plataforma.\n\n"
            "Em Utilizadores listas toda a gente registada. Podes filtrar por tipo (cliente, vendedor, "
            "admin), sexo, estado activo ou bloqueado, e ordenar por nome ou data. Se alguém fizer "
            "malícia, bloqueias a conta — mas não podes bloquear a tua própria.\n\n"
            "Em Estabelecimentos vês todas as lojas da plataforma, não só as tuas. Abres o detalhe e "
            "tens mapa, dados completos, quem é o dono, quantos produtos tem. Podes bloquear a loja ou "
            "bloquear o dono ali mesmo, se for preciso.\n\n"
            "Em Administradores geres quem tem o mesmo poder que tu: promoves alguém pelo email (tem de "
            "já ter conta registada) ou despromoves. Não te podes despromover a ti próprio, nem podes "
            "tirar o último administrador activo — senão ficava ninguém a gerir o sistema.",
        ),
        (
            "O que podes e o que não podes fazer como administrador",
            2,
            "Podes:\n"
            "— Ver estatísticas e listas de toda a plataforma.\n"
            "— Bloquear e desbloquear utilizadores e estabelecimentos.\n"
            "— Promover e despromover outros administradores.\n"
            "— Consultar o detalhe completo de qualquer loja, com mapa.\n\n"
            "Não podes:\n"
            "— Criar contas por aqui — a pessoa tem de se registar primeiro.\n"
            "— Apagar definitivamente utilizadores ou lojas — só bloquear.\n"
            "— Bloquear-te a ti próprio ou ficar sem administradores.\n"
            "— Gerir produtos no lugar dos vendedores — isso é no painel /vendedor/.\n"
            "— Usar o Django Admin clássico (/admin/) — nem está activo neste projecto.",
        ),
        (
            "Um resumo antes de ires embora",
            1,
            "Cliente: entras, pesquisas, vês lojas, guardas favoritos, comentas. Simples.\n\n"
            "Vendedor: tudo isso mais o teu painel para registar loja na Beira, pôr produtos e ler "
            "comentários. Precisas de 18 anos.\n\n"
            "Administrador: não é para o público — geres contas, lojas e outros admins em /gestao/.\n\n"
            "Se tiveres os dois papéis de cliente e vendedor, alternas entre eles conforme o que queres "
            "fazer naquele momento. A Mob foi feita para isso — procurar de manhã, gerir a loja à tarde.\n\n"
            "Qualquer dúvida, pensa sempre: «estou a procurar algo?» → parte pública. «estou a gerir o "
            "meu negócio?» → painel vendedor. «estou a cuidar da plataforma?» → /gestao/.\n\n"
            "Boa sorte — e boas vendas, ou boas compras, conforme o teu lado.",
        ),
    ]


def generate_pdf(output_path: Path) -> None:
    try:
        from fpdf import FPDF
    except ImportError as exc:
        raise SystemExit(
            "Instale fpdf2: pip install fpdf2"
        ) from exc

    if not FONT_REGULAR.exists():
        raise SystemExit(f"Fonte não encontrada: {FONT_REGULAR}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()

    pdf.add_font("Arial", "", str(FONT_REGULAR))
    pdf.add_font("Arial", "B", str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR))
    pdf.add_font("Arial", "I", str(FONT_ITALIC if FONT_ITALIC.exists() else FONT_REGULAR))

    margin = 18
    pdf.set_left_margin(margin)
    pdf.set_right_margin(margin)
    page_width = pdf.w - 2 * margin

    def write_title(text: str, level: int) -> None:
        if level == 0:
            pdf.set_font("Arial", "B", 20)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(page_width, 10, text)
            pdf.ln(2)
        elif level == 1:
            pdf.ln(4)
            pdf.set_font("Arial", "B", 14)
            pdf.set_text_color(185, 28, 28)
            pdf.multi_cell(page_width, 8, text)
            pdf.ln(1)
        else:
            pdf.ln(2)
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(page_width, 7, text)
            pdf.ln(1)

    def write_body(text: str) -> None:
        if not text.strip():
            return
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(page_width, 5.5, text)
        pdf.ln(1)

    # Capa
    pdf.add_page()
    pdf.ln(35)
    pdf.set_font("Arial", "B", 26)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(page_width, 12, "Plataforma Mob", align="C")
    pdf.ln(4)
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(page_width, 8, "Como usar a plataforma — explicado em conversa", align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(
        page_width,
        6,
        "Do cadastro ao painel de administração,\ncomo se alguém te estivesse a guiar.\n\nBeira, Moçambique · 2026",
        align="C",
    )

    pdf.add_page()
    for title, level, body in build_sections():
        if level == 0:
            continue
        if pdf.get_y() > 250 and level <= 2:
            pdf.add_page()
        write_title(title, level)
        write_body(body)

    pdf.set_y(-15)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 10, "Mob — Guia em linguagem natural", align="C")

    pdf.output(str(output_path))
    print(f"PDF gerado: {output_path}")


def generate_markdown(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Como usar a Mob",
        "",
        "*Um guia em linguagem natural — como se estivesse a explicar a alguém ao pé de ti.*",
        "",
    ]
    for title, level, body in build_sections():
        if level == 1:
            lines.append(f"## {title}")
            lines.append("")
        elif level == 2:
            lines.append(f"### {title}")
            lines.append("")
        if body.strip():
            lines.append(body)
            lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Markdown gerado: {output_path}")


if __name__ == "__main__":
    generate_markdown(OUTPUT_MD)
    generate_pdf(OUTPUT_PDF)
