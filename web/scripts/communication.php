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
         return explode(';',$response);
      }

      function getUtilization($group) {
         $this->connect();
         $this->send("INVOKE GROUP ".$group." UTILIZATION");
         $response = $this->receive();
         $this->close();
         if ($response == '') {return array();}
         return explode(';',$response);
      }

      function getClusterList() {
         $this->connect();
         $this->send("INVOKE CONTROL GET_CLUSTER_LIST");
         $response = $this->receive();
         $this->close();
         if ($response == '') {return array();}
         return explode(';',$response);
      }

      function SaveStats($group) {
         session_start();
         $date = new DateTime();
         $sysinfo = $this->getSysInfo($group);
         $utilization = $this->getUtilization($group);
         if (!file_exists('data/' . $_SESSION['uuid'] . '/')) {
            mkdir('data/' . $_SESSION['uuid'] . '/', 0755, true);
         }
	 $file = "data/" . $_SESSION['uuid'] . "/" . $group . $date->getTimeStamp() . ".dat";
         $contents = "";
         for ($i=0;$i<count($sysinfo);$i++) {
            $sysvalue = $sysinfo[$i];
            $sysitems = explode(':', substr($sysvalue, 1, -1));
            $utilvalue = $utilization[$i];
            $utilitems = explode(':', substr($utilvalue, 1, -1));
            $contents .= "<div class=\"nodeinfo\"><h2>Node " . ($i+1) . "</h2><br>";
            $contents .= "IP Address: " . $sysitems[0] . "<br>Operating system: " . $sysitems[1] . "<br>Kernel: " . $sysitems[2] . "<br><br>";
            $contents .= "Total RAM: <strong>" . round($utilitems[1] / 1024) . "</strong> MB<br>Free RAM: <strong>" . round($utilitems[2] / 1024) . "</strong> MB<br>Load AVG: <strong>" . $utilitems[3] . "</strong> (1 min), <strong>" . $utilitems[4] . "</strong> (5 min), <strong>" . $utilitems[5] . "</strong> (15 min)</div>";
         }
         file_put_contents($file, $contents);
         return $file;
      }
   }
?>
