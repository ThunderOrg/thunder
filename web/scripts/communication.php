<?php
   class Communication {
      var $sock;
      function Communication() {}

      function connect() {
         $this->sock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
         socket_connect($this->sock, $_SERVER['SERVER_ADDR'], 6667);
      }

      function close() {
         socket_close($this->sock);
      }

      function send($msg) {
         socket_send($this->sock, $msg, strLen($msg), 0);
      }

      function receive() {
         socket_recv($this->sock, $buf, 1024, 0);
         return $buf;
      }

      function getSysInfo($group) {
         $this->connect();
         $this->send("INVOKE GROUP ".$group." SYSINFO");
         $response = $this->receive();
         $this->close();
         if ($response == '') {return array();}
         return explode('\;',$response);
      }

      function getClusterList() {
         $this->connect();
         $this->send("INVOKE CONTROL GET_CLUSTER_LIST");
         $response = $this->receive();
         $this->close();
         if ($response == '') {return array();}
         return explode('\;',$response);
      }
   
      function parseResponse($msg) {
         
      }
   }
?>
