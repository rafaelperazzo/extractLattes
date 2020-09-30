<?php
//header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Origin: https://sci02-ter-jne.ufca.edu.br");
$DB_DIR = '/usr/src/app/csv/extractLattes.sqlite3';
$db = new SQLite3($DB_DIR);
$db->enableExceptions(true);
header("Content-Type: application/json; charset=UTF-8");
if (isset($_GET['tabela'])) {
    $tabela = $_GET['tabela'];
    try {
        $res = $db->query("SELECT * FROM $tabela ORDER BY ano");
        $linhas = array();
        while ($linha = $res->fetchArray(SQLITE3_ASSOC)) {
            $linhas[] = $linha; 
        }
        print(json_encode($linhas));
    }
    catch (Exception $e) {
        print(json_encode (json_decode ("[]")));
    }
}
else {
    print(json_encode (json_decode ("[]")));
}


?>
