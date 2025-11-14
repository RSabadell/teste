' ==========================================
' INSTRUÇÕES DE INSTALAÇÃO:
' ==========================================
' 1. Baixe JsonConverter.bas de: https://raw.githubusercontent.com/VBA-tools/VBA-JSON/master/JsonConverter.bas
' 2. No Excel, pressione Alt+F11 para abrir o VBA
' 3. Vá em File > Import File e importe o JsonConverter.bas
' 4. Vá em Tools > References e marque "Microsoft Scripting Runtime"
' 5. Cole este código em um novo módulo
' ==========================================


' ==========================================
' VERSÃO OTIMIZADA COM CONTROLE DE NÍVEIS
' ==========================================
Sub ExtrairJSON_MultiNivel()
    Dim ws As Worksheet
    Dim wsDestino As Worksheet
    Dim ultimaLinha As Long
    Dim i As Long
    Dim jsonTexto As String
    Dim jsonObj As Object
    Dim linhaDestino As Long
    Dim colunaJSON As Long
    Dim primeiraLinha As Long
    Dim separador As String
    Dim nivelMaximo As Integer
    Dim chaves() As Variant
    Dim dados() As Variant
    Dim listaObjetos As Collection
    Dim listaExpansoes As Collection
    Dim todasChaves As Object
    Dim valoresExpandidos As Object
    Dim chave As Variant
    Dim col As Long
    Dim rowIdx As Long
    Dim oldCalc As XlCalculation
    Dim oldStatusBar As Variant

    ' CONFIGURAÇÕES
    Set ws = ThisWorkbook.Sheets("json")
    colunaJSON = 1
    primeiraLinha = 2
    separador = "."
    nivelMaximo = 3 ' limite fixo solicitado

    Application.ScreenUpdating = False
    Application.EnableEvents = False
    oldCalc = Application.Calculation
    Application.Calculation = xlCalculationManual
    oldStatusBar = Application.DisplayStatusBar
    Application.DisplayStatusBar = True

    On Error GoTo RestaurarEstado

    ' Remove planilha de destino, se existir
    Application.DisplayAlerts = False
    On Error Resume Next
    ThisWorkbook.Sheets("JSON_MultiNivel").Delete
    On Error GoTo RestaurarEstado
    Application.DisplayAlerts = True

    Set wsDestino = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
    wsDestino.Name = "JSON_MultiNivel"

    ultimaLinha = ws.Cells(ws.Rows.Count, colunaJSON).End(xlUp).Row

    Set todasChaves = CreateObject("Scripting.Dictionary")
    Set listaObjetos = New Collection
    Set listaExpansoes = New Collection

    Application.StatusBar = "Normalizando JSON..."

    For i = primeiraLinha To ultimaLinha
        jsonTexto = Trim$(ws.Cells(i, colunaJSON).Value)
        If Len(jsonTexto) > 0 Then
            Set jsonObj = Nothing
            On Error Resume Next
            Set jsonObj = JsonConverter.ParseJson(jsonTexto)
            On Error GoTo RestaurarEstado

            If Not jsonObj Is Nothing Then
                listaObjetos.Add jsonObj
                Set valoresExpandidos = NormalizarChaves(jsonObj, "", separador, nivelMaximo, 0)
                listaExpansoes.Add valoresExpandidos

                For Each chave In valoresExpandidos.Keys
                    If Not todasChaves.Exists(chave) Then
                        todasChaves.Add chave, todasChaves.Count + 1
                    End If
                Next chave
            End If
        End If
    Next i

    If todasChaves.Count = 0 Then
        MsgBox "Nenhum JSON válido encontrado!", vbExclamation
        GoTo RestaurarEstado
    End If

    chaves = todasChaves.Keys

    ' Cabeçalho
    ReDim dados(1 To 1, 1 To todasChaves.Count)
    For col = LBound(chaves) To UBound(chaves)
        dados(1, col - LBound(chaves) + 1) = chaves(col)
    Next col
    wsDestino.Range(wsDestino.Cells(1, 1), wsDestino.Cells(1, todasChaves.Count)).Value = dados

    ' Dados
    ReDim dados(1 To listaExpansoes.Count, 1 To todasChaves.Count)
    For rowIdx = 1 To listaExpansoes.Count
        Set valoresExpandidos = listaExpansoes(rowIdx)
        For col = 1 To todasChaves.Count
            chave = chaves(col - 1 + LBound(chaves))
            If valoresExpandidos.Exists(chave) Then
                dados(rowIdx, col) = valoresExpandidos(chave)
            Else
                dados(rowIdx, col) = ""
            End If
        Next col
    Next rowIdx

    With wsDestino
        linhaDestino = listaExpansoes.Count + 1
        .Range(.Cells(2, 1), .Cells(linhaDestino, todasChaves.Count)).NumberFormat = "@"
        .Range(.Cells(2, 1), .Cells(linhaDestino, todasChaves.Count)).Value = dados
        .Rows(1).Font.Bold = True
        .Rows(1).Interior.Color = RGB(200, 200, 200)
        .Columns.AutoFit
    End With

    MsgBox "JSON normalizado com sucesso!" & vbCrLf & _
           "Registros: " & listaObjetos.Count & vbCrLf & _
           "Colunas: " & todasChaves.Count & vbCrLf & _
           "Níveis expandidos: " & nivelMaximo, vbInformation

RestaurarEstado:
    Application.ScreenUpdating = True
    Application.EnableEvents = True
    Application.Calculation = oldCalc
    Application.DisplayStatusBar = oldStatusBar
    Application.StatusBar = False

    If Err.Number <> 0 Then
        MsgBox "Erro ao processar JSON: " & Err.Description, vbCritical
    End If
End Sub

Function NormalizarChaves(ByVal obj As Variant, ByVal prefixo As String, _
                          ByVal separador As String, ByVal nivelMaximo As Integer, _
                          ByVal nivelAtual As Integer) As Object
    Dim resultado As Object
    Dim chave As Variant
    Dim novoNome As String
    Dim valorObj As Variant
    Dim subDict As Object
    Dim indice As Long
    Dim item As Variant

    Set resultado = CreateObject("Scripting.Dictionary")

    Select Case TypeName(obj)
        Case "Dictionary"
            For Each chave In obj.Keys
                If prefixo = "" Then
                    novoNome = CStr(chave)
                Else
                    novoNome = prefixo & separador & CStr(chave)
                End If

                valorObj = obj(chave)

                If IsObject(valorObj) Then
                    If TypeName(valorObj) = "Dictionary" Then
                        If nivelAtual < nivelMaximo Then
                            Set subDict = NormalizarChaves(valorObj, novoNome, separador, nivelMaximo, nivelAtual + 1)
                            Call CopiarItens(subDict, resultado)
                        Else
                            resultado(novoNome) = JsonConverter.ConvertToJson(valorObj)
                        End If
                    ElseIf TypeName(valorObj) = "Collection" Then
                        If nivelAtual < nivelMaximo Then
                            indice = 1
                            For Each item In obj(chave)
                                Set subDict = NormalizarChaves(item, novoNome & separador & indice, separador, nivelMaximo, nivelAtual + 1)
                                Call CopiarItens(subDict, resultado)
                                indice = indice + 1
                            Next item
                        Else
                            resultado(novoNome) = JsonConverter.ConvertToJson(obj(chave))
                        End If
                    Else
                        resultado(novoNome) = JsonConverter.ConvertToJson(obj(chave))
                    End If
                Else
                    If IsNull(valorObj) Or IsEmpty(valorObj) Then
                        resultado(novoNome) = ""
                    Else
                        resultado(novoNome) = valorObj
                    End If
                End If
            Next chave

        Case "Collection"
            indice = 1
            For Each item In obj
                Set subDict = NormalizarChaves(item, prefixo & separador & indice, separador, nivelMaximo, nivelAtual + 1)
                Call CopiarItens(subDict, resultado)
                indice = indice + 1
            Next item

        Case Else
            If prefixo <> "" Then
                resultado(prefixo) = obj
            End If
    End Select

    Set NormalizarChaves = resultado
End Function

Private Sub CopiarItens(ByVal origem As Object, ByRef destino As Object)
    Dim chave As Variant
    For Each chave In origem.Keys
        destino(chave) = origem(chave)
    Next chave
End Sub
