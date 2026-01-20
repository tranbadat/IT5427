$InputPath = "."
$OutputPath = "data\\processed"
$WordsPath = "configs\\sensitive_words.txt"
$TextCols = "title,content,description,tags"

python src\\filter_sensitive.py `
  --input $InputPath `
  --output $OutputPath `
  --words $WordsPath `
  --text-cols $TextCols


python filter_sensitive.py --input /home/loc/Downloads/VNPT/crawl_threads/crawl_threads/src/output --output /home/loc/Downloads/VNPT/btl_du_lieu_lon/IT5427/data --words /home/loc/Downloads/VNPT/btl_du_lieu_lon/IT5427/configs/sensitive_words.txt