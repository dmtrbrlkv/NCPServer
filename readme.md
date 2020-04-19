## NCPServer
NCPServer - это простой сервер на базе Flask и библиотеки NotesComPy, позволяюший отдавать данные из баз notes в JSON формате. Запрос данных происходит в REST API стиле. Конфигурация доступных баз и данных хранится в файле config.json

#### Установка
pip install ncpserver-0.1.tar.gz

#### Запуск
nspserver -c path\to\config.json


#### Конфигурация

Базовая конфигурация:
```
{
    "global_session": true,
    "password": "",
    "url": "/notes",
    "port": 9090,
    "separator": "##",
    "log": null,
    "log_format": "[%(asctime)s] %(levelname).1s %(message)s",
    "log_date": "%Y.%m.%d %H:%M:%S",
    "debug": true,
    "databases": {
        "names":{
            "filepath": "names.nsf",
            "server": "PyLN",
            "methods": {
                "view": {"People": "People"},
                "search": false,
                "document": false
            },
            "doc_info": {
                "fields": false
            }
        }
    }
}
```

* password - пароль от user.id, от имени которго будет работать сервер
* url - путь, по которому будет доступен сервер
* port - порт, по которому будет доступен сервер
* separator - разделитель для разделение полей, свойств и формул в заголовках запросов
* log, log_format , log_date - лог-файл и формат сообщений
* debug - запуск Flask в режиме отладки
* databases - доступные для сервера базы

##### Конфигурация доступных баз
* "names" - часть url, по которому будет доступна база 
* filepath, server - сервер и пусть до notes-базы
* methods - доступные запросы к базе
    * search - доступен поиск по формуле
    * document - доступны документы по universalid
    * view - доступные представления в формате "url": "название представления в базе"
* doc_info - данные, доступные для документа
    * fields - получение полей документа
    * properties - получение свойтв документа
    * formulas - вычисление формул
    
#### Полyчение данных

Рассмотрим сервер с конфигурацией баз:
```
    "databases": {
        "names":{
            "filepath": "names.nsf",
            "server": "PyLN",
            "methods": {
                "view": {"People": "People"},
                "search": false,
                "document": false
            },
            "doc_info": {
                "fields": false
            }
        },

        "itcrowd":{
            "filepath": "itcrowd.nsf",
            "server": "PyLN",
            "methods": {
                "view": {"PersonsByLanguages": "Persons\\By language", "Levels": "Levels"},
                "search": true,
                "document": true
            },
            "doc_info": {
                "fields": true,
                "properties": true,
                "formulas": true
            }
        }
    }
```

* Информация о доступных базах и методах - GET запрос на url http://host:port/<базовый url>

`GET 'http://127.0.0.1:5000/notes/'`
```
{
    "itcrowd": {
        "doc_info": {
            "fields": true,
            "formulas": true,
            "properties": true
        },
        "methods": {
            "document": true,
            "search": true,
            "view": [
                "PersonsByLanguages",
                "Levels"
            ]
        }
    },
    "names": {
        "doc_info": {
            "fields": false
        },
        "methods": {
            "document": false,
            "search": false,
            "view": [
                "People"
            ]
        }
    }
}
```

* Информация о базе - GET запрос на url базы

`GET 'http://127.0.0.1:5000/notes/itcrowd'`
```
{
    "Documents": 21,
    "Size": 884736.0
}
```

* Информация о документе - GET запрос на url http://host:port/<базовый url>/<имя базы>/document/<universalid>
    
    Заголовки:
    * `fields: Form##UNID` - поля
    * `properties: Universalid` - свойства
    * `formulas: @Created##@DbTitle` - формулы


`GET 'http://127.0.0.1:5000/notes/itcrowd/document/9A899214038E229843258541003BFFDB' --header 'fields: Form##UNID' --header 'properties: Universalid' --header 'formulas: @Created##@DbTitle'`
```
{
    "@Created": [
        "Sun, 05 Apr 2020 13:55:21 GMT"
    ],
    "@DbTitle": [
        "IT Crowd"
    ],
    "Form": [
        "Person"
    ],
    "UNID": [
        "9A899214038E229843258541003BFFDB"
    ],
    "Universalid": "9A899214038E229843258541003BFFDB"
}
```

* Поиск по формуле - GET запрос на url http://host:port/<базовый url>/<имя базы>/search

     Заголовки:
    * `search_formula: ` - формула поиска
    * `fields: ` - поля
    * `properties: ` - свойства
    * `formulas: ` - формулы
    
`GET 'http://127.0.0.1:5000/notes/itcrowd/search' --header 'search_formula: @contains(FullName; "John")' --header 'fields: FullName##Languages##Level'`

```
{
    "45A4A1F61B47769443258541003609B3": {
        "FullName": [
            "John Smith"
        ],
        "Languages": [
            "Python"
        ],
        "Level": [
            "Middle"
        ]
    },
    "DFBCDDFEE3D0764C432585410046CFFE": {
        "FullName": [
            "John Cena"
        ],
        "Languages": [
            ""
        ],
        "Level": [
            "Senior"
        ]
    }
}
```

* Отбор по представлению - GET запрос на url http://host:port/<базовый url>/<имя базы>/view/<имя представления>

     Заголовки:
    * `keys: ` - ключи отбора
    * `fields: ` - поля
    * `properties: ` - свойства
    * `formulas: ` - формулы
    
    Если поля, свойства и формулы не переданы, то данные возвращаются так, как они отображаются в представлении
    
`GET 'http://127.0.0.1:5000/notes/itcrowd/view/Levels' --header 'keys: Junior'`

```
{
    "8C5A8BCE0F3666A84325854100363E5D": {
        "Created": "Sun, 05 Apr 2020 12:52:29 GMT",
        "Description": [
            "Juniors usually get the least complex tasks, those with little impact on the final product."
        ],
        "Form": [
            "Level"
        ],
        "Level": [
            "Junior"
        ],
        "UNID": [
            "8C5A8BCE0F3666A84325854100363E5D"
        ],
        "UniversalId": "8C5A8BCE0F3666A84325854100363E5D"
    }
}
```
