$InputPath = "."
$OutputPath = "data\\processed"
$WordsPath = "configs\\sensitive_words.txt"
$TextCols = "title,content,description,tags"

python src\\filter_sensitive.py `
  --input $InputPath `
  --output $OutputPath `
  --words $WordsPath `
  --text-cols $TextCols
