<?php
   $s = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
   socket_connect($s, $_SERVER['SERVER_ADDR'], 6667);
   $msg = "INVOKE GROUP PRIMARY_COMPUTE STATUS";
   socket_send($s, $msg, strLen($msg), 0);
   socket_recv($s, $buf, 1024, 0);
   socket_close($s);
   echo($buf)
?>
