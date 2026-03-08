--
-- PostgreSQL database cluster dump
--

\restrict 3i8M4pRPluhlyHPzdDzx2ebCJbdL6QjbeLU18N6We1iVGNuLl6t9DKCWT1XPOuf

SET default_transaction_read_only = off;

SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;

--
-- Roles
--

CREATE ROLE showbuild;
ALTER ROLE showbuild WITH SUPERUSER INHERIT CREATEROLE CREATEDB LOGIN REPLICATION BYPASSRLS PASSWORD 'md5f59b9617642823c0d3336b62ded32c05';




\unrestrict 3i8M4pRPluhlyHPzdDzx2ebCJbdL6QjbeLU18N6We1iVGNuLl6t9DKCWT1XPOuf

--
-- PostgreSQL database cluster dump complete
--

