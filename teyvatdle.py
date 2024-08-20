import sqlite3
import random
import typoguesser
from PIL import Image, ImageDraw


class Character:
    attributes = ["name", "version"]
    
    def __init__(self, ID, name, version):
        self.ID = ID
        self.name = name
        self.version = version

    def compareTo(self, guess):
        common = {key: 1 for key in self.attributes}
        self_dict, guess_dict = vars(self), vars(guess)

        for attribute in common:
            common[attribute] = self_dict[attribute] == guess_dict[attribute]
        else:
            if not common["version"] and \
            self_dict["version"][0] == guess_dict["version"][0]:
                common["version"] = 0.5
        
        return common
    
    def newCompareImage(self, guess, common):
        guess_dict = vars(guess)

        cards = dict()
        size = (256, 256)
        for attr in common:
            c = cards[attr] = dict()
            match common[attr]:
                case 0:
                    background = "darkred"
                case 0.5:
                    background = "gold"
                case 1:
                    background = "green"

            c["img"] = self.textCard(attr, c, size, background, guess)
            if not c["img"]:
                c["foreground"] = Image.open(f"icons/{guess_dict[attr].replace(" ","_")}_Icon.png").convert('RGBA')
                c["background"] = Image.new("RGBA", size, background)
                c["img"] = Image.alpha_composite(c["background"], c["foreground"])

        fullsize = (1635, 920)
        c_y = int(fullsize[1]*.75 - size[1]/2)
        c_x = 0 # initial (first card's left x)
        c_sep = 19
        title_y = (c_y - c_sep*2.5)

        image = Image.new("RGBA", fullsize)
        texts = ImageDraw.Draw(image)
        # texts.text((fullsize[0]//2, fullsize[1]//4), guess.name, fill=(30, 20, 10), anchor="mm", stroke_width=20, stroke_fill=(96, 64, 48), font_size=150)
        texts.text(
            (fullsize[0]//2, fullsize[1]//4),
            guess.name,
            fill=(240, 220, 200),
            anchor="mm",
            stroke_width=20,
            stroke_fill=(96, 64, 48),
            font_size=150
        )
        texts.rectangle([(c_x,title_y-c_sep*1.25),((len(cards)*(size[0]+c_sep))-c_sep-1,title_y+c_sep*1.25)], "white")

        for c in cards:
            if c != "name":
                texts.text(
                    ((c_x + size[0]//2), title_y),
                    c,
                    fill=(96, 64, 48),
                    anchor="mm",
                    stroke_width=2,
                    stroke_fill=(96, 64, 48),
                    font_size=34
                )

            card = cards[c]["img"]
            image.paste(card, (c_x, c_y), card.convert('RGBA'))
            c_x += card.width + c_sep

        # image.show()
        image.save(f"temp/tvd_guess.png", "PNG")

    @staticmethod
    def textCard(attr, card, size, background, guess):
        guess_dict = vars(guess)

        if attr == "version":
            strokewidth = 2
            textsize = 50 * strokewidth

            card["img"] = Image.new("RGBA", size, background)
            foreground = ImageDraw.Draw(card["img"])
            foreground.text(
                (size[0]/2,size[1]/2),
                guess_dict[attr],
                "white",
                anchor="mm",
                stroke_width=strokewidth,
                font_size=textsize
            )
            return card["img"]

        return False

    def __repr__(self):
        return f"({self.ID:0>3}) {self.name}"
    
    def __str__(self):
        return self.name
    
    @staticmethod
    def random():
        return random.choice(getCharacters())
    
    @staticmethod
    def exists(name):
        return typoguesser.guessFrom(getNames(), name)
    
    @staticmethod
    def completeName(name):
        matches = 0
        for char in getCharacters():
            if name in char.name:
                matches += 1
                fullname = char.name

        if matches == 1:
            return fullname
        return False
    

class GenshinChar(Character):
    attributes = Character.attributes + ["nation", "height", "vision", "weapon"]
    attributes.append(attributes.pop(1)) # Move the version attribute to the end

    def __init__(self, ID, name, height, vision, weapon, nation, version):
        super().__init__(ID, name, version)
        self.nation = nation
        self.height = height
        self.vision = vision
        self.weapon = weapon

    def compareTo(self, guess):
        self_dict, guess_dict = vars(self), vars(guess)

        common = super().compareTo(guess)
        if not common["height"] and \
        "Medium" in (self_dict["height"], guess_dict["height"]):
            common["height"] = 0.5

        self.newCompareImage(guess, common)
        return common

    @staticmethod
    def textCard(attr, card, size, background, guess):
        guess_dict = vars(guess)

        if attr == "height" or attr == "version":
            strokewidth = 1 + (attr == "version")
            textsize = 50 * strokewidth

            card["img"] = Image.new("RGBA", size, background)
            foreground = ImageDraw.Draw(card["img"])
            foreground.text(
                (size[0]/2,size[1]/2),
                guess_dict[attr],
                "white",
                anchor="mm",
                stroke_width=strokewidth,
                font_size=textsize
            )
            return card["img"]

        return False


def insertCharacter(name, vision, weapon, nation, height, version):
    try:
        con = sqlite3.connect('genshindle.db')
        c = con.cursor()

        c.execute("""
            INSERT INTO Character
                (name, height, vision, weapon, nation, version)
            VALUES (?, ?, ?, ?, ?, ?)
            """,(name, height, vision, weapon, nation, version))
        con.commit()
            
    finally:    
        c.close()
        con.close()
    

def getCharacters(**conditions):
    try:
        con = sqlite3.connect('genshindle.db')
        c = con.cursor()
        
        keys = "name LIKE ?"
        values = ['%']
        for key in conditions:
            if key in GenshinChar.attributes:
                keys += f" AND {key} = ?"
                values.append(conditions[key].title())

        c.execute(f"""
            SELECT *
            FROM Character 
            WHERE {keys}
            """, tuple(values))
                
        return [GenshinChar(*attrs) for attrs in c.fetchall()]
    finally:    
        c.close()
        con.close()


def getNames():
    names = [char.name for char in getCharacters()]
    for name in names:
        parts = name.split()
        if len(parts) > 1:
            names += parts

    return sorted(names)


if __name__ == "__main__":

    # for name in [
    #     "htu aop",
    #     "wansnfdere",
    #     "qing qiu",
    #     "ayaka",
    #     "at9oi",
    #     "aytop",
    #     "benente",
    #     "artlechino",
    #     "baxiuso",
    #     "furina",
    #     "eual",
    #     "komai",
    #     "riande",
    #     "vent",
    #     "albfeido",
    #     "chidç",
    #     "ganye",
    #     "moiano",
    #     "sheneh",
    #     "nahidne",
    #     "anvia",
    #     "niaou",
    #     "cyno",
    #     "clorinde",
    #     "chiopri",
    #     "zhonglu",
    #     "wyelam n",
    #     "xiao",
    #     "xiuanyn",
    #     "beidouy",
    #     "candece",
    #     "chungiuy´n",
    #     "goirou",
    #     "abrbab",
    #     "amebrer",
    #     "coleii",
    #     "faruzna",
    #     "gmiang",
    #     "raozer",
    #     "yun jun",
    #     "neole",
    #     "thoiama",
    #     "sucrosne",
    #     "heizoqu",
    #     "dioru",
    #     "klerr",
    #     "jwan",
    #     "ittro",
    #     "sehya",
    #     "filuc",
    #     "alhtaitham",
    #     "lunye"
    # ]:
    #     print(name, typoguesser.guessFrom(getNames(), name, max_missing=2), sep=": ")

    print(GenshinChar.random().compareTo(GenshinChar.random()))
