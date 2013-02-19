<?php
class Authorization {
   var $username;
   var $passhash;
   var $connection;
   var $db;
   var $pwd;
   var $table;
   var $site_name;
   var $error_message;
   var $role;

   function Authorization() {
      $this->site_name = "CARE Cloud";
   }

   function InitDB($host, $uname, $pwd, $db, $table) {
      $this->db_host = $host;
      $this->username = $uname;
      $this->pwd = $pwd;
      $this->db = $db;
      $this->table = $table;
   }

   function DBLogin() {
      $this->connection = mysql_connect($this->db_host, $this->username, $this->pwd);
      if (!$this->connection) {
         $this->HandleDBError("Could not connect to database!");
         return false;
      }
      if (!mysql_select_db($this->db, $this->connection)) {
         $this->HandleDBError("Could not select database!");
         return false;
      }
      if (!mysql_query("SET NAMES 'UTF8'", $this->connection)) {
         $this->HandleDBError("Could not set encoding to UTF8");
         return false;
      }
      return true;
   }

   function Login() {
      if (empty($_POST['username'])) {
         $this->HandleError("Username is empty!");
         return false;
      }
      if (empty($_POST['password'])) {
         $this->HandleError("Password is empty!");
         return false;
      }
      $username = trim($_POST['username']);
      $passhash = hash("sha256", trim($_POST['password']));
      if (!$this->CheckLoginInDB($username, $passhash)) {
         return false;
      }

      if (!isset($_SESSION)) {
         session_start();
      }

      $_SESSION['username'] = $username;
      $_SESSION['uuid'] = uniqid();
     
      return true;
   }

   function GetLoginSessionVar() {
      if (isset($_SESSION[$this->username])) {
         $ret = $_SESSION[$this->username];
      } else {
         $ret = false;
      }
      return $ret;
   }

   function Logout() {
      session_start();
      $sessionvar = $this->GetLoginSessionVar();
      $_SESSION['uuid']=NULL;
      unset($_SESSION['uuid']);
      header("Location: index.php");
   }

   function Redirect($url) {
      header("Location: $url");
      exit;
   }
   
   function CheckLoginInDB($username, $passhash) {
      if (!isset($_SESSION)) {
         session_start();
      }
      if (!$this->DBLogin()) {
         $this->HandleError("Database login failed!");
         return false;
      }
      $username = $this->SanitizeForSQL($username);
      $sql = "select fname, lname, role from user where username='$username' and password='$passhash'";

      $res = mysql_query($sql, $this->connection);

      if (!$res || mysql_num_rows($res) <= 0) {
         $this->HandleError("The username or password are incorrect");
         return false;
      } else {
         $vals = mysql_fetch_assoc($res);
         $_SESSION['role'] = $vals['role'];
         $_SESSION['name'] = $vals['fname'].' '.$vals['lname'];
      }
      return true;
   }

   function CheckLogin() {
      session_start();
      if (empty($_SESSION['uuid'])) {
         return false;
      }
      return true;
   }

   function GetRole() {
      if (isset($_SESSION['role'])) {
         return $_SESSION['role'];
      } else {
         return -1;
      }
   }

   function GetName() {
      if (isset($_SESSION['name'])) {
         return $_SESSION['name'];
      } else {
         return "unknown";
      }
 
   }

   function SanitizeForSQL($str) {
      if (function_exists("mysql_real_escape_string")) {
         $ret = mysql_real_escape_string($str);
      } else {
         $ret = addslashes($str);
      }
      return $ret;
   }

   function Sanitize($str, $remove_nl=true) {
      $str = $this->StripSlashes($str);
      
      if ($remove_nl) {
         $injections = array('/(\n+)/i', '/(\r+)/i', '/(\t+)/i', '/(%0A+)/i', '/(%0D+)/i', '/(%08+)/i', '/(%09+)/i');
         $str = preg_replace($injections,'',$str);
      }
      return $str;
   }

   function StripSlashes($str) {
      if (get_magic_quotes_gpc()) {
         $str = stripslashes($str);
      }
      return $str;
   }

   function GetSelfScript() {
      return htmlentities($_SERVER['PHP_SELF']);
   }

   function GetErrorMessage() {
      if (empty($this->error_message)) {
         return '';
      }
      $errmsg = nl2br(htmlentities($this->error_message));
      return $errmsg;
   }

   function ClearError() {
      $this->error_message = '';
   }  
 
   function HandleError($msg) {
      // To do: Log error
      $this->error_message = $msg."\r\n";
   }

   function HandleDBError($msg) {
      // To do: Log Error
      $this->HandleError($msg);
   }
}
?>
