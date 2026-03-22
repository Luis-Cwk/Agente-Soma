// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract SomaArt is ERC721, Ownable {
    uint256 private _tokenIdCounter;

    constructor() ERC721("SomaArt", "SOMA") Ownable(msg.sender) {}

    function mint(address to, string memory uri) public onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter;
        _tokenIdCounter += 1;
        _safeMint(to, tokenId);
        return tokenId;
    }

    function _baseURI() internal pure override returns (string memory) {
        return "ipfs://";
    }
}
