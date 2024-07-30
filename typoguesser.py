class Match:
    def __init__(self, word, guess):
        self.word = word
        self.lenDiff = ((len(guess) - len(word))**2)**0.5
        self.anagram = False
        self.substrScore = 0
        self.match_qty = 0
        self.mismatch_qty = 0
        self.mism_sides = {'nw':0, 'n':0, 'ne':0,
                            'w':0, '?':0, 'e':0,
                           'sw':0, 's':0, 'se':0}
        self.eq = self.compare(guess)
        
    def compare(self, guess):
        guess, word = guess.lower(), self.word.lower()
        if word == guess:
            return True
        if sorted(word) == sorted(guess):
            self.anagram = True

        alreadyGuessed = []
        for char in range(max(len(guess), len(word))):
            # substrings "score" updater for loop
            for subleng in range(1, len(word)-char):
                try:
                    substr = word[ char:(char+1+subleng)]
                    if substr in guess:
                        # substring length added to score
                        self.substrScore += len(substr)
                        # substring index offset substracted from score
                        self.substrScore -= ((guess.index(substr) - char)**2)**0.5
                except IndexError:
                    break

            try:
                if guess[char] == word[char] and char not in alreadyGuessed:
                    self.match_qty += 1
                    alreadyGuessed.append(char)
                    continue
                try:
                    if guess[char] == word[char+1] and char+1 not in alreadyGuessed:
                        self.match_qty += 0.34
                        alreadyGuessed.append(char+1)
                        continue
                except IndexError: pass
                try:
                    if guess[char] == word[char-1] and char != 0 and char-1 not in alreadyGuessed:
                        self.match_qty += 0.34
                        alreadyGuessed.append(char+1)
                        continue
                except IndexError: pass
                
                self.mismatch_qty += 1
                self.mism_sides[ isNextTo(word[char],guess[char])] += 1

            except IndexError:
                self.mismatch_qty += 1

        return False     


def isNextTo(letter, other):
    '''Check if letter is next to other in qwerty,
    return where with cardinal points interpreting left as west, etc.
    Otherwise return False.'''
    qwerty = ['1234567890',
            'qwertyuiop',
            'asdfghjkl',
            'zxcvbnm']
    letter, other = letter.lower(), other.lower()
    for l in range(4):
        line = qwerty[l]
        # Find qwerty line where 'letter' is (Y = l)
        if letter in line:
            # Find column where 'letter' is (X = c)
            c = line.index(letter)
            # Compare 'other' to the 8 letters around 'letter'
            # [from previous(-1) to next(+1) c(olumn) and l(ine)]
            for i in range(c - 1, c + 2):
                for j in range(l - 1, l + 2):
                    try:
                        if i < 0 or j < 0:
                            raise IndexError
                        # Find the difference of "coords" between the letters
                        # and return 'other''s corresponding cardinal point
                        if qwerty[j][i] == other:
                            match (i - c, j - l):
                                case (0, -1):
                                    return "n"
                                case (1, -1):
                                    return "ne"
                                case (1, 0):
                                    return "e"
                                case (1, 1):
                                    return "se"
                                case (0, 1):
                                    return "s"
                                case (-1, 1):
                                    return "sw"
                                case (-1, 0):
                                    return "w"
                                case (-1, -1):
                                    return "nw"
                    except IndexError:
                        continue
            break
    return "?"


def getFilteredWords(words, startWith = False, min_length = 1, max_length = 1000):
    filtering = 0
    while filtering < len(words):
        word = words[filtering]
        if startWith:
            try:
                if word.index(startWith) != 0:
                    raise ValueError
            except ValueError:
                words.remove(word)
                continue
        if len(word) < min_length or len(word) > max_length:
            words.remove(word)
        else:
            filtering += 1

    return words


def guessFrom(words, string, minimum = 0.5, max_missing = 1, max_extra = 1):
    if string in words:
        return string
    
    # Find and compare best matches for 'string' in 'words'    
    matches = []
    anagrams = []
    for word in getFilteredWords(words,
                    max_length=(len(string) + max_extra),
                    min_length=(len(string) - max_missing)
                ):
        current = Match(word, string)
        if current.eq:
            return word
        elif current.anagram:
            anagrams.append(current)

        mismSides_values = sorted(list(current.mism_sides.values()))
        if (len(word) * minimum > current.match_qty
        or len(word) * (1-minimum) <= current.mismatch_qty
        or (len(word) > 3 and current.match_qty < 2.5)
        or current.match_qty < 1.5
        or current.mism_sides["?"] > mismSides_values[-2] + 1
        or mismSides_values.count(0) < 6):
            del current
        else:
            matches.append(current)

    # Return false if the minimum requirements given for a "match" weren't met
    if len(matches) == 0:
        try:
            bestmatch = anagrams[0]
        except IndexError:
            return False
    
    # Reduce the list of matches to the potentially best one
    best_farSides = -1
    prevLen = len(matches)
    while len(matches) >= 1:
        bestmatch = matches.pop()
        while len(matches) >= 1:
            nextmatch = matches[-1]
            # break = next is better | continue = next is worse
            
            # 1st priority comparison
            if nextmatch.substrScore > bestmatch.substrScore + 1:
                break
            
            if (nextmatch.match_qty > bestmatch.match_qty
            or nextmatch.mismatch_qty < bestmatch.mismatch_qty):
                break
            if (nextmatch.match_qty < bestmatch.match_qty
            or nextmatch.mismatch_qty > bestmatch.mismatch_qty):
                matches.pop()
                continue

            # 2nd priority comparison
            if nextmatch.lenDiff < bestmatch.lenDiff:
                break
            if nextmatch.lenDiff > bestmatch.lenDiff:
                matches.pop()
                continue

            # 3rd priority comparison
            check_sides = [nextmatch.mism_sides]
            if best_farSides == -1:  # (first iteration)
                check_sides.insert(0, bestmatch.mism_sides)
            for checking in check_sides:
                non0sides = []
                far_sides = 0
                for side in checking:
                    if checking[side] != 0:
                        non0sides.append((side, checking[side]))
                        for n0s in non0sides:
                            if (side == "?"
                            or (n0s[0][0] != side[0] and n0s[0][-1] != side[-1])):
                                far_sides += 1
                else:
                    if best_farSides == -1:  # (first iteration)
                        best_farSides = far_sides
                    
            if (far_sides < best_farSides or
                list(nextmatch.mism_sides.values()).count(0)
                > list(bestmatch.mism_sides.values()).count(0)
            ):
                best_farSides = far_sides
                break
            if (far_sides > best_farSides or
                list(nextmatch.mism_sides.values()).count(0)
                < list(bestmatch.mism_sides.values()).count(0)
            ):
                matches.pop()
                continue

            if prevLen == len(matches):
                if len(anagrams) > 1 and nextmatch not in anagrams:
                    matches.pop()
                    continue
                else:
                    break
            else:
                prevLen = len(matches)

    else:
        if (bestmatch.mismatch_qty / len(bestmatch.word) > 0.4
        and len(anagrams) > 0):
                return anagrams.pop().word
        return bestmatch.word
