package standard is

  type boolean is (false, true);
  type bit is ('0','1');
  
  type character is (
		nul, soh, stx, etx, eot, enq, ack, bel, 
		bs,  ht,  lf,  vt,  ff,  cr,  so,  si, 
		dle, dc1, dc2, dc3, dc4, nak, syn, etb, 
		can, em,  sub, esc, fsp, gsp, rsp, usp, 

		' ', '!', '"', '#', '$', '%', '&', ''', 
		'(', ')', '*', '+', ',', '-', '.', '/', 
		'0', '1', '2', '3', '4', '5', '6', '7', 
		'8', '9', ':', ';', '<', '=', '>', '?', 

		'@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 
		'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 
		'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 
		'X', 'Y', 'Z', '[', '\', ']', '^', '_', 

		'`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 
		'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 
		'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 
		'x', 'y', 'z', '{', '|', '}', '~', del);

  type severity_level is (note, warning, error, failure);

  type integer is range -2147483648 to 2147483647;
  subtype natural is integer range 0 to integer'high;
  subtype positive is integer range 1 to integer'high;

  type REAL is range -1.0E+38 to +1.0E+38;

  type bit_vector is array (natural range <>) of bit;
  type string is array (positive range <>) of character; 
  type file_open_kind is (read_mode, write_mode, append_mode);
  type file_open_status is (open_ok, status_error, name_error, mode_error);

  --attribute foreign: string;
  
  type time is range -9223372036854775808 to 9223372036854775807
  units
    fs;             -- femtosecond
    ps = 1000 fs;   -- picosecond
    ns = 1000 ps;   -- nanosecond
    us = 1000 ns;   -- microsecond
    ms = 1000 us;   -- millisecond
    sec = 1000 ms;  -- second
    min = 60 sec;   -- minute
    hr = 60 min;    -- hour
  end units;
  
  subtype delay_length is time range 0 ps to time'high;
  
  impure function now return delay_length; 
 
end standard;
