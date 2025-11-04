-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Tempo de geração: 04-Nov-2025 às 13:43
-- Versão do servidor: 10.4.32-MariaDB
-- versão do PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `mygeli`
--

-- --------------------------------------------------------

--
-- Estrutura da tabela `historico_uso`
--

CREATE TABLE `historico_uso` (
  `id_historico` int(11) NOT NULL,
  `nome_receita` varchar(255) NOT NULL,
  `nome_ingrediente` varchar(255) NOT NULL,
  `quantidade_usada` decimal(10,2) NOT NULL,
  `unidade_medida` varchar(50) DEFAULT NULL,
  `data_hora_uso` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `login_tokens`
--

CREATE TABLE `login_tokens` (
  `token_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `selector` varchar(255) NOT NULL,
  `hashed_token` varchar(255) NOT NULL,
  `expires` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `login_tokens`
--

INSERT INTO `login_tokens` (`token_id`, `user_id`, `selector`, `hashed_token`, `expires`) VALUES
(1, 2, '2a5432b76b2ae324377f1cbc6457bfbc', 'a0d0a9ad0591724ec69410fc15924a840ed602eecc52522844e8b451cfb33a08', '2025-10-10 15:27:46'),
(2, 2, 'd9e85dd707e839fe64fe85fb970fac87', '9bacb275f007d8d564f1aa439179b7cdd2343ba7a63614b1f538ae18da0b2b84', '2025-10-10 16:27:15'),
(4, 5, '13992fc029abb139052c7ad06c27adbd', '8f759e20604e1e7c10d9e0477fd36309ee1ff64525c6eb926dcefa7cbf5796de', '2025-12-04 12:37:24');

-- --------------------------------------------------------

--
-- Estrutura da tabela `produtos`
--

CREATE TABLE `produtos` (
  `id_produto` int(3) UNSIGNED ZEROFILL NOT NULL,
  `user_id` int(11) NOT NULL,
  `nome_produto` varchar(100) NOT NULL,
  `quantidade_produto` decimal(10,2) UNSIGNED NOT NULL,
  `tipo_volume` varchar(12) NOT NULL,
  `valor_energetico_kcal` decimal(10,2) DEFAULT NULL,
  `acucares_totais_g` decimal(10,2) DEFAULT NULL,
  `acucares_adicionados_g` decimal(10,2) DEFAULT NULL,
  `carboidratos_g` decimal(10,2) DEFAULT NULL,
  `proteinas_g` decimal(10,2) DEFAULT NULL,
  `gorduras_totais_g` decimal(10,2) DEFAULT NULL,
  `gorduras_saturadas_g` decimal(10,2) DEFAULT NULL,
  `gorduras_trans_g` decimal(10,2) DEFAULT NULL,
  `fibra_alimentar_g` decimal(10,2) DEFAULT NULL,
  `sodio_g` decimal(10,2) DEFAULT NULL,
  `data_criacao` timestamp NOT NULL DEFAULT current_timestamp(),
  `data_modificacao` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `produtos`
--

INSERT INTO `produtos` (`id_produto`, `user_id`, `nome_produto`, `quantidade_produto`, `tipo_volume`, `valor_energetico_kcal`, `acucares_totais_g`, `acucares_adicionados_g`, `carboidratos_g`, `proteinas_g`, `gorduras_totais_g`, `gorduras_saturadas_g`, `gorduras_trans_g`, `fibra_alimentar_g`, `sodio_g`, `data_criacao`, `data_modificacao`) VALUES
(011, 5, 'Caqui', 3.00, 'Unidades', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2025-11-04 12:39:10', '2025-11-04 12:39:10');

-- --------------------------------------------------------

--
-- Estrutura da tabela `receitas`
--

CREATE TABLE `receitas` (
  `idreceita` int(3) NOT NULL,
  `tituloreceita` varchar(100) NOT NULL,
  `descreceita` text NOT NULL,
  `idusuario` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura da tabela `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `nome` varchar(255) DEFAULT NULL,
  `telefone` varchar(30) DEFAULT NULL,
  `email` varchar(255) NOT NULL,
  `senha` varchar(255) NOT NULL,
  `preferencias` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Extraindo dados da tabela `usuarios`
--

INSERT INTO `usuarios` (`id`, `nome`, `telefone`, `email`, `senha`, `preferencias`) VALUES
(2, 'Luis Otavio', '19999999999', 'tevinho@gmail.com', '$2y$10$XdRmRirHIPOD4mU2wDzg1O5lkesoDXOVpz5Bf5bRRWnuu5fyYs2Ie', NULL),
(3, 'Jose', '19987654356', 'jose_silva@gmail.com', 'scrypt:32768:8:1$Zy0KvEkUNa1BlcYO$3eaef6f1ec54805d907d6c75f00b4abd38eee8183fbc864114a0d012f9eb7c94b077c9b361ef9ad8c373536605739a97941fc991e67a0ba1c41faecf3c4c7f4c', NULL),
(4, 'Tilambo Rego', '19999999999', 'tilambo.rego@gmail.com', 'scrypt:32768:8:1$AWI6ekcPl0l1N71X$26ed6252160afd096641d5d3967d5566d6cbba8c7ac2361302b54ae43438800bbb3fb315084c93875a5a89baa871dbe56f3988d0e6359cf1fec13f741c01b55f', NULL),
(5, 'Marvin Cristhian Gomes Pinto', '19984214178', 'marvin@gmail.com', 'scrypt:32768:8:1$9Lty904GH3UZyPRY$37b36529fa0b3ecf51b029fbc53ee10ff5bb757639da6d54fd7d22dc220a8cb17d8679be2466f6b308ba0cbbdbcccdeaaab791eba28da8e734449413bf77d3a0', '{\"allergies\": \"a comida\", \"dietary_restrictions\": \"nao posso comer nada solido e nada liquido\", \"other\": \"prefiro comidas plasticas\"}');

--
-- Índices para tabelas despejadas
--

--
-- Índices para tabela `login_tokens`
--
ALTER TABLE `login_tokens`
  ADD PRIMARY KEY (`token_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Índices para tabela `produtos`
--
ALTER TABLE `produtos`
  ADD PRIMARY KEY (`id_produto`),
  ADD UNIQUE KEY `nome_produto` (`nome_produto`),
  ADD KEY `user_id` (`user_id`);

--
-- Índices para tabela `receitas`
--
ALTER TABLE `receitas`
  ADD PRIMARY KEY (`idreceita`),
  ADD KEY `fk_receita_usuario` (`idusuario`);

--
-- Índices para tabela `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT de tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `login_tokens`
--
ALTER TABLE `login_tokens`
  MODIFY `token_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de tabela `produtos`
--
ALTER TABLE `produtos`
  MODIFY `id_produto` int(3) UNSIGNED ZEROFILL NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de tabela `receitas`
--
ALTER TABLE `receitas`
  MODIFY `idreceita` int(3) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Restrições para despejos de tabelas
--

--
-- Limitadores para a tabela `login_tokens`
--
ALTER TABLE `login_tokens`
  ADD CONSTRAINT `login_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Limitadores para a tabela `produtos`
--
ALTER TABLE `produtos`
  ADD CONSTRAINT `produtos_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`);

--
-- Limitadores para a tabela `receitas`
--
ALTER TABLE `receitas`
  ADD CONSTRAINT `fk_receita_usuario` FOREIGN KEY (`idusuario`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
