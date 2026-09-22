"""Display translations for stable undo action IDs (never stored in snapshots)."""

# Columns: action ID, French, German, Italian, Spanish, Portuguese, Hebrew.
_ROWS = """
attach.new|Nouveau brin dessiné|Neuen Strang gezeichnet|Disegnato un nuovo filo|Hebra nueva dibujada|Novo fio desenhado|צויר גדיל חדש
attach.child|Brin attaché|Strang angehängt|Collegato un filo|Hebra conectada|Fio conectado|חובר גדיל
move.strand|Point déplacé|Punkt verschoben|Spostato un punto|Punto movido|Ponto movido|הוזזה נקודה
rotate.strand|Brin tourné|Strang gedreht|Ruotato un filo|Hebra girada|Fio girado|סובב גדיל
angle.adjust|Angle/longueur ajustés|Winkel/Länge angepasst|Modificati angolo/lunghezza|Ángulo/longitud ajustados|Ângulo/comprimento ajustados|הותאמו זווית ואורך
mask.create|Masque créé|Maske erstellt|Creata una maschera|Máscara creada|Máscara criada|נוצרה מסכה
mask.edit|Masque modifié|Maske bearbeitet|Modificata una maschera|Máscara editada|Máscara editada|נערכה מסכה
layer.add|Brin ajouté|Strang hinzugefügt|Aggiunto un filo|Hebra añadida|Fio adicionado|נוסף גדיל
layer.delete|Calque supprimé|Ebene gelöscht|Eliminato un livello|Capa eliminada|Camada excluída|נמחקה שכבה
layer.delete_all|Canevas effacé|Zeichenfläche geleert|Svuotata l’area di disegno|Lienzo vaciado|Tela limpa|נוקה משטח הציור
layer.reorder|Calques réordonnés|Ebenen neu angeordnet|Riordinati i livelli|Capas reordenadas|Camadas reordenadas|שונה סדר השכבות
layer.lock|Verrouillage du calque modifié|Ebenensperre geändert|Modificato il blocco del livello|Bloqueo de capa cambiado|Bloqueio da camada alterado|שונתה נעילת שכבה
layer.clear_locks|Tous les verrous supprimés|Alle Sperren aufgehoben|Rimossi tutti i blocchi|Todos los bloqueos eliminados|Todos os bloqueios removidos|בוטלו כל הנעילות
layer.lock_mode|Mode verrouillage basculé|Sperrmodus umgeschaltet|Attivata/disattivata modalità blocco|Modo de bloqueo alternado|Modo de bloqueio alternado|שונה מצב הנעילה
layer.select|Sélection modifiée|Auswahl geändert|Modificata la selezione|Selección cambiada|Seleção alterada|שונתה הבחירה
strand.color|Couleur du brin modifiée|Strangfarbe geändert|Modificato il colore del filo|Color de hebra cambiado|Cor do fio alterada|שונה צבע הגדיל
strand.circle_stroke|Contour du cercle modifié|Kreisumrandung geändert|Modificato il contorno del cerchio|Contorno del círculo cambiado|Contorno do círculo alterado|שונה קו המתאר של העיגול
strand.end_circle_stroke|Contour du cercle d’extrémité modifié|Endkreisumrandung geändert|Modificato il contorno del cerchio finale|Contorno del círculo final cambiado|Contorno do círculo final alterado|שונה קו המתאר של עיגול הקצה
strand.hidden|Visibilité du calque basculée|Ebenensichtbarkeit umgeschaltet|Modificata la visibilità del livello|Visibilidad de capa alternada|Visibilidade da camada alternada|שונתה נראות השכבה
strand.shadow_only|Ombre seule basculée|Nur-Schatten umgeschaltet|Attivata/disattivata solo ombra|Solo sombra alternada|Somente sombra alternada|שונה מצב צל בלבד
strand.hide_shadow|Masquage de l’ombre basculé|Schattenausblendung umgeschaltet|Modificata la visibilità dell’ombra|Ocultación de sombra alternada|Ocultação da sombra alternada|שונתה הסתרת הצל
strand.line_visible|Visibilité de la ligne basculée|Liniensichtbarkeit umgeschaltet|Modificata la visibilità della linea|Visibilidad de línea alternada|Visibilidade da linha alternada|שונתה נראות הקו
strand.extension|Ligne d’extension basculée|Verlängerungslinie umgeschaltet|Attivata/disattivata linea di estensione|Línea de extensión alternada|Linha de extensão alternada|שונתה הצגת קו ההארכה
strand.circle_visible|Cercle d’extrémité basculé|Endkreis umgeschaltet|Attivato/disattivato cerchio finale|Círculo final alternado|Círculo final alternado|שונתה הצגת עיגול הקצה
strand.arrow|Flèche basculée|Pfeil umgeschaltet|Attivata/disattivata freccia|Flecha alternada|Seta alternada|שונתה הצגת חץ
strand.arrow_style|Style de flèche modifié|Pfeilstil geändert|Modificato lo stile della freccia|Estilo de flecha cambiado|Estilo da seta alterado|שונה סגנון החץ
strand.reset_mask|Masque réinitialisé|Maske zurückgesetzt|Reimpostata una maschera|Máscara restablecida|Máscara redefinida|אופסה מסכה
strand.close_knot|Nœud fermé|Knoten geschlossen|Chiuso un nodo|Nudo cerrado|Nó fechado|נסגר קשר
strand.paste|Données du brin collées|Strangdaten eingefügt|Incollati i dati del filo|Datos de hebra pegados|Dados do fio colados|הודבקו נתוני גדיל
strand.width|Largeur du brin modifiée|Strangbreite geändert|Modificata la larghezza del filo|Ancho de hebra cambiado|Largura do fio alterada|שונה רוחב הגדיל
strand.end_style|Extrémité stylisée|Endseite gestaltet|Modificato lo stile dell’estremità|Estilo del extremo cambiado|Estilo da extremidade alterado|שונה עיצוב הקצה
strand.shadow|Ombre du brin modifiée|Strangschatten bearbeitet|Modificata l’ombra del filo|Sombra de hebra editada|Sombra do fio editada|נערך צל הגדיל
group.create|Groupe créé|Gruppe erstellt|Creato un gruppo|Grupo creado|Grupo criado|נוצרה קבוצה
group.delete|Groupe supprimé|Gruppe gelöscht|Eliminato un gruppo|Grupo eliminado|Grupo excluído|נמחקה קבוצה
group.rename|Groupe renommé|Gruppe umbenannt|Rinominato un gruppo|Grupo renombrado|Grupo renomeado|שונה שם הקבוצה
group.move|Groupe déplacé|Gruppe verschoben|Spostato un gruppo|Grupo movido|Grupo movido|הוזזה קבוצה
group.rotate|Groupe tourné|Gruppe gedreht|Ruotato un gruppo|Grupo girado|Grupo girado|סובבה קבוצה
group.angle|Angles du groupe modifiés|Gruppenwinkel bearbeitet|Modificati gli angoli del gruppo|Ángulos del grupo editados|Ângulos do grupo editados|נערכו זוויות הקבוצה
group.shadow|Ombre du groupe modifiée|Gruppenschatten bearbeitet|Modificata l’ombra del gruppo|Sombra del grupo editada|Sombra do grupo editada|נערך צל הקבוצה
group.edit|Groupe modifié|Gruppe bearbeitet|Modificato un gruppo|Grupo editado|Grupo editado|נערכה קבוצה
system.load|Document chargé|Dokument geladen|Caricato un documento|Documento cargado|Documento carregado|נטען מסמך
system.new|Nouveau document|Neues Dokument|Nuovo documento|Documento nuevo|Novo documento|מסמך חדש
system.setting|Paramètre modifié|Einstellung geändert|Modificata un’impostazione|Configuración cambiada|Configuração alterada|שונתה הגדרה
system.unknown|Modification|Änderung|Modifica|Cambio|Alteração|שינוי
move.endpoint|Extrémité déplacée|Endpunkt verschoben|Spostata un’estremità|Extremo movido|Extremidade movida|הוזזה נקודת קצה
move.control_point|Point de contrôle déplacé|Kontrollpunkt verschoben|Spostato un punto di controllo|Punto de control movido|Ponto de controle movido|הוזזה נקודת בקרה
"""

ACTION_TRANSLATIONS = {lang: {} for lang in ('fr', 'de', 'it', 'es', 'pt', 'he')}
for _row in _ROWS.strip().splitlines():
    _action, *_labels = _row.split('|')
    for _lang, _label in zip(ACTION_TRANSLATIONS, _labels):
        ACTION_TRANSLATIONS[_lang][_action] = _label

# Additional application languages, in the same action order as above.
_EXTRA = {
    'ru': """Нарисована новая прядь|Прикреплена прядь|Перемещена точка|Повёрнута прядь|Изменены угол/длина|Создана маска|Изменена маска|Добавлена прядь|Удалён слой|Холст очищен|Изменён порядок слоёв|Изменена блокировка слоя|Сняты все блокировки|Переключён режим блокировки|Изменено выделение|Изменён цвет пряди|Изменён контур круга|Изменён контур конечного круга|Изменена видимость слоя|Переключён режим только тени|Изменено скрытие тени|Изменена видимость линии|Переключена линия продолжения|Переключён конечный круг|Переключена стрелка|Изменён стиль стрелки|Маска сброшена|Узел замкнут|Вставлены данные пряди|Изменена ширина пряди|Изменён стиль конца|Изменена тень пряди|Создана группа|Удалена группа|Группа переименована|Группа перемещена|Группа повёрнута|Изменены углы группы|Изменена тень группы|Группа изменена|Документ загружен|Новый документ|Изменена настройка|Изменение|Перемещена конечная точка|Перемещена контрольная точка""",
    'ja': """新しいストランドを描画|ストランドを接続|点を移動|ストランドを回転|角度・長さを調整|マスクを作成|マスクを編集|ストランドを追加|レイヤーを削除|キャンバスをクリア|レイヤーの順序を変更|レイヤーのロックを切り替え|すべてのロックを解除|ロックモードを切り替え|選択を変更|ストランドの色を変更|円の輪郭を変更|端の円の輪郭を変更|レイヤーの表示を切り替え|影のみの表示を切り替え|影の非表示を切り替え|線の表示を切り替え|延長線を切り替え|端の円を切り替え|矢印を切り替え|矢印のスタイルを変更|マスクをリセット|結び目を閉じる|ストランドのデータを貼り付け|ストランドの幅を変更|端のスタイルを変更|ストランドの影を編集|グループを作成|グループを削除|グループ名を変更|グループを移動|グループを回転|グループの角度を編集|グループの影を編集|グループを編集|ドキュメントを読み込み|新規ドキュメント|設定を変更|変更|端点を移動|制御点を移動""",
    'zh': """绘制了新绳股|连接了绳股|移动了点|旋转了绳股|调整了角度和长度|创建了遮罩|编辑了遮罩|添加了绳股|删除了图层|清空了画布|调整了图层顺序|切换了图层锁定|清除了所有锁定|切换了锁定模式|更改了选择|更改了绳股颜色|更改了圆的描边|更改了端点圆的描边|切换了图层可见性|切换了仅显示阴影|切换了阴影隐藏|切换了线条可见性|切换了延长线|切换了端点圆|切换了箭头|更改了箭头样式|重置了遮罩|闭合了结|粘贴了绳股数据|更改了绳股宽度|更改了端部样式|编辑了绳股阴影|创建了组|删除了组|重命名了组|移动了组|旋转了组|编辑了组角度|编辑了组阴影|编辑了组|加载了文档|新建文档|更改了设置|更改|移动了端点|移动了控制点""",
    'sv': """Ritade en ny tråd|Fäste en tråd|Flyttade en punkt|Roterade en tråd|Justerade vinkel/längd|Skapade en mask|Redigerade en mask|Lade till en tråd|Raderade ett lager|Rensade arbetsytan|Ändrade lagerordningen|Ändrade lagerlåsning|Tog bort alla lås|Växlade låsläge|Ändrade markeringen|Ändrade trådfärg|Ändrade cirkelkontur|Ändrade ändcirkelns kontur|Växlade lagersynlighet|Växlade endast skugga|Växlade dold skugga|Växlade linjesynlighet|Växlade förlängningslinje|Växlade ändcirkel|Växlade pil|Ändrade pilstil|Återställde en mask|Slöt en knut|Klistrade in tråddata|Ändrade trådbredd|Ändrade ändstil|Redigerade trådskugga|Skapade en grupp|Raderade en grupp|Bytte gruppnamn|Flyttade en grupp|Roterade en grupp|Redigerade gruppvinklar|Redigerade gruppskugga|Redigerade en grupp|Läste in ett dokument|Nytt dokument|Ändrade en inställning|Ändring|Flyttade en ändpunkt|Flyttade en kontrollpunkt""",
    'fi': """Piirrettiin uusi säie|Liitettiin säie|Siirrettiin pistettä|Kierrettiin säiettä|Säädettiin kulmaa/pituutta|Luotiin maski|Muokattiin maskia|Lisättiin säie|Poistettiin taso|Tyhjennettiin piirtoalue|Muutettiin tasojen järjestystä|Muutettiin tason lukitusta|Poistettiin kaikki lukitukset|Vaihdettiin lukitustilaa|Muutettiin valintaa|Muutettiin säikeen väriä|Muutettiin ympyrän reunaviivaa|Muutettiin pääty-ympyrän reunaviivaa|Vaihdettiin tason näkyvyyttä|Vaihdettiin vain varjo -tilaa|Vaihdettiin varjon piilotusta|Vaihdettiin viivan näkyvyyttä|Vaihdettiin jatkoviivan näkyvyyttä|Vaihdettiin pääty-ympyrän näkyvyyttä|Vaihdettiin nuolen näkyvyyttä|Muutettiin nuolen tyyliä|Nollattiin maski|Suljettiin solmu|Liitettiin säikeen tiedot|Muutettiin säikeen leveyttä|Muutettiin päädyn tyyliä|Muokattiin säikeen varjoa|Luotiin ryhmä|Poistettiin ryhmä|Nimettiin ryhmä uudelleen|Siirrettiin ryhmää|Kierrettiin ryhmää|Muokattiin ryhmän kulmia|Muokattiin ryhmän varjoa|Muokattiin ryhmää|Ladattiin asiakirja|Uusi asiakirja|Muutettiin asetusta|Muutos|Siirrettiin päätepistettä|Siirrettiin ohjauspistettä""",
}
for _lang, _text in _EXTRA.items():
    ACTION_TRANSLATIONS[_lang] = dict(zip(ACTION_TRANSLATIONS['fr'], _text.split('|')))
