def count_words(file_path):
    words_count = {}
    with open(file_path) as file:
        for line in file:
            words = line.split()
            for word in words:
                try:
                    words_count[word] += 1
                except KeyError:
                    words_count[word] = 1
    return words_count


print(count_words('alis.txt')["\n"])