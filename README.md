# Идея 

Деанонимизация пользователей BitShares/Graphene блокчейнов может являться более простой задачей чем задача 
деанонимизации пользователей Bitcoin в силу закрепленности аккаунта за пользователем (единичного раскрытия личности 
достаточно, например при переводе на аккаунт с карты в 
обменнике). 

Отсюда решено попробовать решить задачу связки владельца Bitcoin кошелька с пользователем на BitShares/Graphene.

Данное ПО предназначено для отслеживания пользователей BitShares/Graphene чейнов за пределами данных чейнов,
основываясь на наблюдениях за шлюзами.

По найденным транзакциям можно пробовать устанавливать адреса кошельков пользователя с дальнейшим 
построением простых графов связей переводов. Кроме того, после установки достаточного количества адресов шлюза, 
возможно использовать эти данные при дальнейшей линковке пользователей.
 
# Описание
Сопоставление и сбор Bitcoin адресов пользователей BitShares блокчейна для последующего анализа и деанонимизации 
пользователей. 

Возможно расширение для Etherium переводов (как и других публичных бч).

Для поиска данных по транзакциям использовалось API Blockchair (несколько простых функций для запроса реализовано 
мною, blockchair не предоставляет библиотеки для python). 

Задачи и результаты складываются в MongoDB, в таблицы tasks и txs:
 * В tasks находятся сами объекты задач для дальнейшей обработки (поиска транзакций).
 * В txs находятся результаты линковки пользователей BitShares с хешами их транзакцией на блокчейне Bitcoin.

# Развертка 
Готовый Dockerfile для развертки приложения, порт MongoDB пробрасывается наружу на 27018 порт, для избежаний коллизий с уже установленной монгой на хосте (если есть).
``` 
git clone https://gitlab.com/dmantis/gateway_watcher
cd gateway_watcher
docker build -t gateway_watcher . 
docker run -p 127.0.0.1:27018:27017 --name gw -t gateway_watcher
```

# Автор
tg @dmantis