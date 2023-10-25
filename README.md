Запуск проекта

1. Установить Rasa: `pip3.9 install rasa`
2. Добавить библиотеку: 
```
pip3 install 'rasa[spacy]'
python3 -m spacy download ru_core_news_sm
```
3. Обучить модель: `rasa train`
4. Запустить обученную модель в терминале: `rasa shell`
5. Запустить сервер экшнов: `rasa run actions`

Можно запустить бота в интерактивном режиме: `rasa interactive`. Если возникают ошибки в процессе,
может помочь такое: `pip3.9 uninstall uvloop`

Запустить тесты:
`rasa run actions; rasa train; rasa test`